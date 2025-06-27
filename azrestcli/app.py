from flask import Flask, request, jsonify
import subprocess
import json
import os
import threading
import time

app = Flask(__name__)

CONFIG_PATH = "/data/options.json"
OUTPUT_PATH = "/tmp/az_output.json"

def login():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    tenant_id = config.get("tenant_id")
    client_id = config.get("client_id")
    client_secret = config.get("client_secret")

    login_cmd = [
        "az", "login",
        "--service-principal",
        "--username", client_id,
        "--password", client_secret,
        "--tenant", tenant_id
    ]
    subprocess.run(login_cmd, check=True, capture_output=True)

def run_async_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "timestamp": time.time()
        }, f)

@app.route("/run", methods=["POST"])
def run_az_command():
    try:
        cmd = request.json.get("command")
        if not cmd.startswith("az "):
            return jsonify({"error": "Only 'az' commands are allowed"}), 400

        threading.Thread(target=run_async_command, args=(cmd,)).start()

        return jsonify({"status": "Command started"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/last_result", methods=["GET"])
def get_last_result():
    if not os.path.exists(OUTPUT_PATH):
        return jsonify({"error": "No result found"}), 404
    with open(OUTPUT_PATH) as f:
        return jsonify(json.load(f))

if __name__ == "__main__":
    login()
    app.run(host="0.0.0.0", port=5902)
