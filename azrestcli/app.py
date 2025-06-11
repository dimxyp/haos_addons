from flask import Flask, request, jsonify
import subprocess
import json
import os

app = Flask(__name__)

CONFIG_PATH = "/data/options.json"

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

@app.route("/run", methods=["POST"])
def run_az_command():
    try:
        cmd = request.json.get("command")
        if not cmd.startswith("az "):
            return jsonify({"error": "Only 'az' commands are allowed"}), 400

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return jsonify({
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    login()
    app.run(host="0.0.0.0", port=5902)
