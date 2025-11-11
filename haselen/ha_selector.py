import json
import os
import requests
import subprocess
import sys

OPTIONS_FILE = '/data/options.json'

def load_options():
    with open(OPTIONS_FILE, "r") as f:
        opts = json.load(f)
    for key in ("haip", "token"):
        if key not in opts:
            raise ValueError(f"Missing required option: '{key}'")
    return opts

def get_input_text_value(entity_id, haip, token):
    url = f"https://{haip}:8123/api/states/{entity_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        print(f"Failed to get {entity_id}: {resp.status_code} {resp.text}")
        sys.exit(1)
    state = resp.json().get("state")
    return state

if __name__ == '__main__':
    opts = load_options()
    haip = opts["haip"]
    token = opts["token"]

    # Example: input_text.haselenium
    selector = get_input_text_value("input_text.haselenium", haip, token)
    print(f"input_text.haselenium value: [{selector}]")

    if selector == "zenith":
        print("Launching check_zenith_bill.py ...")
        subprocess.run([sys.executable, "check_zenith_bill.py"], check=True)
    elif selector == "zenithgas":
        print("Launching check_gas_bill.py ...")
        subprocess.run([sys.executable, "check_gas_bill.py"], check=True)
    else:
        print(f"Unrecognized value '{selector}'. Nothing to do.")