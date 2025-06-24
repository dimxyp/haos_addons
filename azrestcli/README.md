# Home Assistant Community Add-on: Azure CLI

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
