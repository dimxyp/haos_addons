# Home Assistant Custom Add-on: Azure CLI

## 🔧 About

This Home Assistant add-on runs **Azure CLI (`az`) commands** sent as **HTTP REST requests**.
Use it to manage Azure resources from Home Assistant with `rest_command` and automations.

---

## 🚀 Features

- Small [Flask](https://flask.palletsprojects.com/) REST server inside the container.
- Signs in with an **Azure Service Principal** when the add-on starts.
- Runs commands **without a shell** (`shlex` + `shell=False`). Only `az` commands are accepted, and `;`, `&&`, `|` do not work
- Runs **one command or a list of commands**, always in order (one batch at a time, so commands never race on the same resource)
- **Async** by default, or **sync** (`"wait": true`) to get the result in the response
- Keeps the last 20 results (`/results`) and logs every command with its return code
- Listens on `127.0.0.1` by default; optional API token
- Each command stops after 300 seconds

---

## ⚙️ Configuration

```yaml
tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
client_secret: "your-client-secret"
listen_host: "127.0.0.1"   # use 0.0.0.0 only if other LAN hosts must call it (set api_token too)
api_token: ""              # optional; when set, every request needs header X-API-Token
```

The port is fixed at **5902**. The add-on uses `host_network`, so Home Assistant reaches it at `http://127.0.0.1:5902`.

Give the service principal only the permissions it needs (for example *Virtual Machine Contributor*, *Network Contributor* on the NSGs, *Storage Account Contributor* on the storage accounts).

---

## 📡 REST API

| Method | Path           | Description                               |
|--------|----------------|-------------------------------------------|
| POST   | `/run`         | Run one command or a list of commands     |
| GET    | `/last_result` | Result of the last command                |
| GET    | `/results`     | Last 20 results                           |

### Payload

```json
{ "command": "az vm list -o json" }
```
```json
{
  "commands": [
    "az storage account update -n mystg -g my-rg --subscription <sub> --remove networkRuleSet.ipRules",
    "az storage account network-rule add --account-name mystg -g my-rg --subscription <sub> --ip-address 1.2.3.4"
  ],
  "wait": true
}
```

If one command fails, the rest of the list still runs.

### Response

Async (default):
```json
{ "status": "Command started", "count": 2 }
```
With `"wait": true`:
```json
{
  "ok": true,
  "results": [
    { "command": "az ...", "stdout": "...", "stderr": "", "returncode": 0, "timestamp": 1762070000.0 }
  ]
}
```
Errors: `400` (no command, or a command that does not start with `az`), `401` (wrong or missing token).

---

## 🏠 Home Assistant `rest_command`

Generic, plus one per action type. Every value is a variable, so nothing is hard-coded:

```yaml
rest_command:
  # data: commands (text or list), wait (optional)
  az_cli:
    url: "http://127.0.0.1:5902/run"
    method: POST
    content_type: application/json
    payload: >-
      {{ {"commands": ([commands] if commands is string else commands | list),
          "wait": wait | default(false) | bool} | to_json }}
    timeout: 300

  # data: vm, rg, subs
  az_vm_start:
    url: "http://127.0.0.1:5902/run"
    method: POST
    content_type: application/json
    payload: >-
      {{ {"commands": ["az vm start --name " ~ vm ~ " -g " ~ rg ~ " --subscription " ~ subs]} | to_json }}

  # data: ip, nsg (name or list), rule, rg, subs
  az_nsg_allow_ip:
    url: "http://127.0.0.1:5902/run"
    method: POST
    content_type: application/json
    payload: >-
      {% set ns = namespace(c=[]) %}
      {% for n in ([nsg] if nsg is string else nsg) %}
      {% set ns.c = ns.c + ["az network nsg rule update --nsg-name " ~ n ~ " -n " ~ rule
          ~ " -g " ~ rg ~ " --subscription " ~ subs ~ " --source-address-prefix " ~ ip] %}
      {% endfor %}{{ {"commands": ns.c} | to_json }}

  # data: ip, account, rg, subs -- replaces ALL ip rules of the account with this ip
  az_storage_allow_ip:
    url: "http://127.0.0.1:5902/run"
    method: POST
    content_type: application/json
    payload: >-
      {{ {"commands": [
          "az storage account update -n " ~ account ~ " -g " ~ rg ~ " --subscription " ~ subs ~ " --remove networkRuleSet.ipRules",
          "az storage account network-rule add --account-name " ~ account ~ " -g " ~ rg ~ " --subscription " ~ subs ~ " --ip-address " ~ ip
      ]} | to_json }}
```

If you set `api_token`, add to each one:
```yaml
    headers:
      X-API-Token: !secret azrestcli_token
```

### Automation examples

```yaml
# Start a VM
- action: rest_command.az_vm_start
  data:
    vm: MY-VM
    rg: MY-RG
    subs: 00000000-0000-0000-0000-000000000000

# Public IP changed -> update NSG rules and storage firewall
- action: rest_command.az_nsg_allow_ip
  data:
    ip: "{{ trigger.to_state.state }}"
    nsg: [VM1-nsg, VM2-nsg]
    rule: SSH
    rg: MY-RG
    subs: 00000000-0000-0000-0000-000000000000
- action: rest_command.az_storage_allow_ip
  data:
    ip: "{{ trigger.to_state.state }}"
    account: mystorageacc
    rg: MY-RG
    subs: 00000000-0000-0000-0000-000000000000

# Any az command, wait for the result
- action: rest_command.az_cli
  data:
    commands: az account show -o json
    wait: true
  response_variable: az
```

---

## 🐳 Dockerfile

- Based on `homeassistant/amd64-base`
- Installs Azure CLI and Flask
- Starts `app.py` (signs in with the service principal, then starts the REST server)

---

## 🔒 Security

- The add-on holds Azure credentials and runs commands with them. Keep `listen_host: 127.0.0.1` unless you need LAN access. If you open it, set `api_token`, and never expose it to the internet.
- Commands run without a shell and must start with `az`.

---

## 📁 Files

- `app.py`: Flask REST API that runs the commands
- `Dockerfile`: builds the container
- `config.yaml`: add-on config and options schema
- `/data/options.json`: credentials and options at runtime (created by Supervisor)

---

✍️ Maintained by dx. Contributions welcome!
