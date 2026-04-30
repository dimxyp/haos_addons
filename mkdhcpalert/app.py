import os
import time
import json
import requests
from datetime import datetime
from routeros_api import RouterOsApiPool

MIKROTIK_HOST = os.getenv("MIKROTIK_HOST", "")
MIKROTIK_USER = os.getenv("MIKROTIK_USER", "")
MIKROTIK_PASS = os.getenv("MIKROTIK_PASS", "")
MIKROTIK_PORT = int(os.getenv("MIKROTIK_PORT", "8728"))
MIKROTIK_USE_SSL = os.getenv("MIKROTIK_USE_SSL", "false").lower() == "true"

HA_URL = os.getenv("HA_URL", "http://homeassistant:8123").rstrip("/")
HA_TOKEN = os.getenv("HA_TOKEN", "")
HA_NOTIFY_SERVICE = os.getenv("HA_NOTIFY_SERVICE", "notify")  # notify.<service>, default notify.notify
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "10"))

STATE_FILE = os.getenv("STATE_FILE", "/data/state.json")

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"seen_ids": []}
    except Exception:
        return {"seen_ids": []}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

def ha_notify(title, message):
    if not HA_TOKEN:
        print("HA_TOKEN missing; skipping notify")
        return

    # service format: notify or mobile_app_xxx etc
    # If user gives "notify" we call notify/notify
    # If user gives "mobile_app_pixel" we call notify/mobile_app_pixel
    domain = "notify"
    service = HA_NOTIFY_SERVICE
    url = f"{HA_URL}/api/services/{domain}/{service}"

    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {"title": title, "message": message}
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    if r.status_code >= 300:
        print(f"Notify failed: {r.status_code} {r.text}")
    else:
        print("Notify sent")

def connect():
    if not (MIKROTIK_HOST and MIKROTIK_USER and MIKROTIK_PASS):
        raise RuntimeError("Missing MikroTik env vars")

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
    # RouterOS API keys can include things like '.id'
    lease_id = l.get(".id") or l.get("id") or ""
    address = l.get("address", "")
    mac = l.get("mac-address", "")
    host = l.get("host-name", "")
    server = l.get("server", "")
    status = l.get("status", "")
    dynamic = l.get("dynamic", "")
    comment = l.get("comment", "")
    return {
        "id": lease_id,
        "address": address,
        "mac": mac,
        "host": host,
        "server": server,
        "status": status,
        "dynamic": dynamic,
        "comment": comment,
    }

def main():
    state = load_state()
    seen_ids = set(state.get("seen_ids", []))

    print("Starting MikroTik DHCP lease watcher")
    print(f"Polling every {POLL_SECONDS}s, state file: {STATE_FILE}")

    pool = None
    api = None

    while True:
        try:
            if pool is None:
                pool = connect()
                api = pool.get_api()

            resource = api.get_resource("/ip/dhcp-server/lease")
            leases = resource.get()

            new_items = []
            for raw in leases:
                lease = normalize_lease(raw)
                if lease["id"] and lease["id"] not in seen_ids:
                    new_items.append(lease)

            if new_items:
                # Mark as seen first to avoid repeat notifications if notify fails and loop restarts
                for lease in new_items:
                    seen_ids.add(lease["id"])
                save_state({"seen_ids": list(seen_ids)})

                for lease in new_items:
                    title = "New DHCP lease (MikroTik)"
                    msg = (
                        f"IP: {lease['address']}\n"
                        f"MAC: {lease['mac']}\n"
                        f"Host: {lease['host']}\n"
                        f"Server: {lease['server']}\n"
                        f"Status: {lease['status']}\n"
                        f"Time: {datetime.now().isoformat(timespec='seconds')}"
                    )
                    print("New lease detected:", lease)
                    ha_notify(title, msg)

            time.sleep(POLL_SECONDS)

        except Exception as e:
            print("Error:", repr(e))
            # Reset connection and retry
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
