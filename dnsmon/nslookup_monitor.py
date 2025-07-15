import json
import os
import subprocess
import requests

IP_STORE_FILE = '/app/ip_store.json'
CONFIG_FILE = '/data/options.json' 
HA_URL = "https://192.168.1.250/core/api/states"

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def load_ip_store():
    if not os.path.exists(IP_STORE_FILE):
        return {}
    with open(IP_STORE_FILE, 'r') as f:
        return json.load(f)

def save_ip_store(store):
    with open(IP_STORE_FILE, 'w') as f:
        json.dump(store, f)

def resolve_ip(domain):
    try:
        result = subprocess.check_output(["nslookup", domain], universal_newlines=True)
        for line in result.splitlines():
            if "Address:" in line and not line.startswith("Server:"):
                return line.split("Address:")[1].strip()
    except Exception as e:
        print(f"Error resolving {domain}: {e}")
    return None

def update_input_text(entity_id, new_ip, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{HA_URL}/{entity_id}"
    data = {
        "state": new_ip
    }
    r = requests.post(url, headers=headers, json=data)
    if r.status_code != 200:
        print(f"Failed to update {entity_id}: {r.text}")

def main():
    config = load_config()
    token = config['token']
    urls = config.get("urls", {})
    store = load_ip_store()
    changed = False

    for key, domain in urls.items():
        entity_id = f"input_text.{key.lower()}"
        ip = resolve_ip(domain)
        if not ip:
            continue
        if store.get(key) != ip:
            update_input_text(entity_id, ip, token)
            store[key] = ip
            changed = True

    if changed:
        save_ip_store(store)

if __name__ == "__main__":
    main()
