import json
import os
import requests
import subprocess
import sys
import warnings
from urllib3.exceptions import InsecureRequestWarning

OPTIONS_FILE = '/data/options.json'

# 1) suppress "Unverified HTTPS request" spam
warnings.simplefilter("ignore", InsecureRequestWarning)

# 2) only show critical by default
QUIET = True
def info(msg):
    if not QUIET:
        print(msg)

def critical(msg):
    print(msg)

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
        critical(f"Failed to get {entity_id}: {resp.status_code} {resp.text}")
        sys.exit(1)
    return resp.json().get("state")

if __name__ == '__main__':
    opts = load_options()
    haip = opts["haip"]
    token = opts["token"]

    selector = get_input_text_value("input_text.haselenium", haip, token)

    # This line is not critical; keep only if you want it visible
    info(f"input_text.haselenium value: [{selector}]")

    try:
        if selector == "zenith":
            info("Launching check_zenith_bill.py ...")
            subprocess.run([sys.executable, "check_zenith_bill.py"], check=True)
        elif selector == "zenithgas":
            info("Launching check_gas_bill.py ...")
            subprocess.run([sys.executable, "check_gas_bill.py"], check=True)
        elif selector == "voltonb21":
            info("Launching check_volton_bill.py ...")
            subprocess.run([sys.executable, "check_volton_bill.py"], check=True)
        else:
            info(f"Unrecognized value '{selector}'. Nothing to do.")
    except subprocess.CalledProcessError as e:
        critical(f"Child script failed: {e}")
        sys.exit(1)