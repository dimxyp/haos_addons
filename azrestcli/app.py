import hmac
import json
import shlex
import subprocess
import threading
import time
from collections import deque

from flask import Flask, jsonify, request

CONFIG_PATH = "/data/options.json"
CMD_TIMEOUT = 300

app = Flask(__name__)
results = deque(maxlen=20)
run_lock = threading.Lock()

with open(CONFIG_PATH) as f:
    config = json.load(f)
API_TOKEN = config.get("api_token") or ""


def login():
    subprocess.run(
        [
            "az", "login", "--service-principal",
            "--username", config["client_id"],
            "--password", config["client_secret"],
            "--tenant", config["tenant_id"],
            "--output", "none",
        ],
        check=True,
        capture_output=True,
    )


def parse(cmd):
    argv = shlex.split(cmd)
    if not argv or argv[0] != "az":
        raise ValueError(f"Only 'az' commands are allowed: {cmd!r}")
    return argv


def run_one(argv):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=CMD_TIMEOUT)
        out = {"stdout": r.stdout, "stderr": r.stderr, "returncode": r.returncode}
    except subprocess.TimeoutExpired:
        out = {"stdout": "", "stderr": "timeout", "returncode": -1}
    out.update(command=shlex.join(argv), timestamp=time.time())
    results.append(out)
    msg = f"[{out['returncode']}] {out['command']}"
    if out["returncode"]:
        msg += "\n" + out["stderr"].strip()
    print(msg, flush=True)
    return out


def run_batch(batch):
    # one at a time, so commands touching the same resource never race
    with run_lock:
        return [run_one(argv) for argv in batch]


def unauthorized():
    return API_TOKEN and not hmac.compare_digest(request.headers.get("X-API-Token", ""), API_TOKEN)


@app.route("/run", methods=["POST"])
def run_az_command():
    if unauthorized():
        return jsonify({"error": "Unauthorized"}), 401
    body = request.get_json(silent=True) or {}
    cmds = body.get("commands") or [body.get("command")]
    try:
        if not all(isinstance(c, str) and c.strip() for c in cmds):
            raise ValueError("No command given")
        batch = [parse(c) for c in cmds]
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if body.get("wait"):
        res = run_batch(batch)
        return jsonify({"ok": all(r["returncode"] == 0 for r in res), "results": res}), 200

    threading.Thread(target=run_batch, args=(batch,), daemon=True).start()
    return jsonify({"status": "Command started", "count": len(batch)}), 200


@app.route("/last_result", methods=["GET"])
def get_last_result():
    if unauthorized():
        return jsonify({"error": "Unauthorized"}), 401
    if not results:
        return jsonify({"error": "No result found"}), 404
    return jsonify(results[-1])


@app.route("/results", methods=["GET"])
def get_results():
    if unauthorized():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(list(results))


if __name__ == "__main__":
    login()
    app.run(host=config.get("listen_host") or "127.0.0.1", port=5902, threaded=True)
