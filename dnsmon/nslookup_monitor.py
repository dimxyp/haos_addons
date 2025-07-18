import json
import os
import socket
import time
import requests
import urllib3
import subprocess
import re
import functools
from datetime import datetime
print = functools.partial(print, flush=True)

def ts() -> str:
    """Return current ts() string."""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OPTIONS_FILE = '/data/options.json'
STORE_FILE = '/data/ip_store.json'

def load_options():
    with open(OPTIONS_FILE) as f:
        return json.load(f)

def load_previous_ips():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE) as f:
            return json.load(f)
    return {}

def save_ips(ip_dict):
    with open(STORE_FILE, 'w') as f:
        json.dump(ip_dict, f)

#old way
# def resolve_ipv4(hostname):
#     try:
#         return socket.gethostbyname(hostname)
#     except Exception as e:
#         print(f"[{ts()}] [ERROR] Could not resolve {hostname}: {e}")
#         return None

def resolve_ipv4(hostname):
    try:
        result = subprocess.run(
            ["dig", "+short", "+time=5", "+tries=2", hostname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        output = result.stdout.strip()

        # Filter for the first IPv4 (ignore empty or IPv6)
        for line in output.splitlines():
            if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', line):
                return line

        print(f"[{ts()}] [ERROR] No valid IPv4 found for {hostname}. Output:\n{output}")
        return None

    except subprocess.TimeoutExpired:
        print(f"[{ts()}] [ERROR] DNS lookup for {hostname} timed out")
    except Exception as e:
        print(f"[{ts()}] [ERROR] Failed to resolve {hostname} using dig: {e}")
    
    return None

def update_input_text(entity_id, value, token, haip):
    url = f"https://{haip}:8123/api/services/input_text/set_value"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "entity_id": entity_id,
        "value": value
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        if response.status_code == 200:
            print(f"[{ts()}] [INFO] Updated {entity_id} to {value}")
        else:
            print(f"[{ts()}] [ERROR] Failed to update {entity_id}: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[{ts()}] [ERROR] API request failed: {e}")

def print_banner():
    print(r"""
     _      
    | |     
  __| |_  __
 / _` \ \/ /
| (_| |>  < 
 \__,_/_/\_\
            
""", flush=True)

# Call the banner function before starting main loop
print_banner()
print(f"[{ts()}] [WELCOME] Custom DNS Monitor started. Version: 0.1.1", flush=True)
print(f"[{ts()}] ====================================================", flush=True)
def main_loop():
    options = load_options()
    haip = options['haip']
    token = options['token']

    previous_ips = load_previous_ips()

    while True:
        changed = False

        for i in range(1, 6):
            url_key = f"URL{i}"
            entity_id = f"input_text.url{i}"
            hostname = options.get(url_key)

            #  Skip unset or "null" entries
            if str(hostname).strip().upper() == "NULL":
                continue

            ip = resolve_ipv4(hostname)
            if not ip:
                continue

            if previous_ips.get(url_key) != ip:
                print(f"[{ts()}] [CHANGE] {hostname} changed from {previous_ips.get(url_key)} to {ip}")
                update_input_text(entity_id, ip, token, haip)
                previous_ips[url_key] = ip
                changed = True
            # else:
            #     print(f"[{ts()}] [OK] {hostname} IP unchanged: {ip}")

        if changed:
            save_ips(previous_ips)

        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    main_loop()
