# Home Assistant Custom Add-on: Azure CLI

## 🔧 About

This Home Assistant add-on allows you to execute **Azure CLI (`az`) commands** remotely via **HTTP REST requests**. It's designed to let you manage and automate Azure resources directly from Home Assistant workflows using `rest_command`, automations, or scripts.

---

## 🚀 Features

- Lightweight [Flask](https://flask.palletsprojects.com/) web server inside the container
- Authenticates with **Azure Service Principal**
- Accepts **secure REST POST** requests to run Azure CLI commands
- Returns output as structured JSON (stdout, stderr, return code)
- Port is configurable via add-on options
- No `nc`, no shell piping — just clean REST calls

---

## ⚙️ Configuration

In the **Home Assistant Add-on UI**, configure the following:

```yaml
tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret: "your-client-secret"
port: 5902
```
Ensure the Azure service principal has the correct permissions for the resources you want to manage.

📡 REST API
After starting the add-on, it listens on the configured port (default 5902).

✅ Endpoint
```yaml
POST http://[addon-ip]:[port]/run
```
🧾 Payload
```yaml
{
  "command": "az vm list --output json"
}
```
🔁 Response
```yaml
{
  "stdout": "[ ... JSON from az command ... ]",
  "stderr": "",
  "returncode": 0
}
```
🏠 Example: Home Assistant rest_command
```yaml
rest_command:
  run_az_command:
    url: "http://192.168.1.50:5902/run"
    method: POST
    headers:
      Content-Type: application/json
    payload: >
      {
        "command": "az vm list --output json"
      }
```
🐳 Dockerfile Highlights
Based on homeassistant/amd64-base

Installs Azure CLI and Flask

Removes broken Azure CLI .bashrc tab-completion

Starts app.py as REST server

🔒 Security Note
This add-on uses your Azure credentials from options.json and exposes a command-execution interface. Make sure the add-on network is secure and not exposed to the internet.

📁 File Structure

app.py – Python Flask REST API that handles command execution

Dockerfile – Builds the container

config.yaml – Home Assistant add-on config schema (in your repo)

options.json – Contains Azure credentials and runtime port

✍️ 
Maintained by dx. Contributions welcome!





















