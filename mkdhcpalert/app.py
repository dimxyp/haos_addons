import os
import time
import json
import requests
from datetime import datetime
from routeros_api import RouterOsApiPool

def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)

MIKROTIK_HOST = env("MIKROTIK_HOST")
MIKROTIK_USER = env("MIKROTIK_USER")
MIKROTIK_PASS = env("MIKROTIK_PASS")
MIKROTIK_PORT = int(env("MIKROTIK_PORT", "8728"))
MIKROTIK_USE_SSL = env("MIKROTIK_USE_SSL", "false").lower() == "true"

HA_URL = env("HA_URL", "http://homeassistant:8123").rstrip("/")
HA_TOKEN = env("HA_TOKEN", "")
HA_NOTIFY_SERVICE = env("HA_NOTIFY_SERVICE", "notify")

POLL_SECONDS = int(env("POLL_SECONDS", "10"))
ONLY_BOUND = env("ONLY_BOUND", "true").lower() == "true"

STATE_FILE = env("STATE_FILE", "/data/state.json")

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"seen_macs": []}
    except Exception:
        return {"seen_macs": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

def ha_notify(title, message):
    if not HA_TOKEN:
        print("HA_TOKEN missing; skipping notify")
        return
    url = f"{HA_URL}/api/services/notify/{HA_NOTIFY_SERVICE}"
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    payload = {"title": title, "message": message}
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    if r.status_code >= 300:
        print(f"Notify failed: {r.status_code} {r.text}")
    else:
        print("Notify sent")

def connect():
    if not (MIKROTIK_HOST and MIKROTIK_USER and MIKROTIK_PASS):
        raise RuntimeError("Missing MikroTik env vars (MIKROTIK_HOST/USER/PASS)")

    pool = RouterOsApiPool(
        MIKROTIK_HOST,
        username=MIKROTIK_USER,
        password=MIKROTIK_PASS,
        port=MIKROTIK_PORT,
        use_ssl=MIKROTIK_USE_SSL,
        ssl_verify=False,
        plaintext_login=True,
    )
    return pool

def normalize_lease(l):
    return {
        "address": l.get("address", ""),
        "mac": l.get("mac-address", ""),
        "host": l.get("host-name", ""),
        "server": l.get("server", ""),
        "status": l.get("status", ""),
    }

def main():
    state = load_state()
    seen_macs = set(m.lower() for m in state.get("seen_macs", []) if isinstance(m, str))

    print("Starting MikroTik DHCP lease watcher")
    print(f"Polling={POLL_SECONDS}s ONLY_BOUND={ONLY_BOUND} MikroTik={MIKROTIK_HOST}:{MIKROTIK_PORT} SSL={MIKROTIK_USE_SSL}")

    pool = None
    api = None

    while True:
        try:
            if pool is None:
                pool = connect()
                api = pool.get_api()

            leases = api.get_resource("/ip/dhcp-server/lease").get()

            new_items = []
            for raw in leases:
                lease = normalize_lease(raw)

                if ONLY_BOUND and lease["status"] != "bound":
                    continue

                mac = (lease["mac"] or "").lower().strip()
                if not mac:
                    continue

                if mac not in seen_macs:
                    new_items.append(lease)

            if new_items:
                for lease in new_items:
                    seen_macs.add((lease["mac"] or "").lower().strip())
                save_state({"seen_macs": sorted(seen_macs)})

                for lease in new_items:
                    title = "New device on DHCP (MikroTik)"
                    msg = (
                        f"IP: {lease['address']}\n"
                        f"MAC: {lease['mac']}\n"
                        f"Host: {lease['host']}\n"
                        f"Server: {lease['server']}\n"
                        f"Status: {lease['status']}\n"
                        f"Time: {datetime.now().isoformat(timespec='seconds')}"
                    )
                    print("New device detected:", lease)
                    ha_notify(title, msg)

            time.sleep(POLL_SECONDS)

        except Exception as e:
            print("Error:", repr(e))
            try:
                if pool:
                    pool.disconnect()
            except Exception:
                pass
            pool = None
            api = None
            time.sleep(5)

if __name__ == "__main__":
    main()
