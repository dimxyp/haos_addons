import json
import os
import time
from datetime import datetime

import requests
from routeros_api import RouterOsApiPool

OPTIONS_FILE = os.getenv("OPTIONS_FILE", "/data/options.json")
STATE_FILE = os.getenv("STATE_FILE", "/data/state.json")


def load_options():
    defaults = {
        "mikrotik_host": "192.168.1.254",
        "mikrotik_port": 8728,
        "mikrotik_user": "apiuser",
        "mikrotik_password": "",
        "mikrotik_use_ssl": False,
        "poll_seconds": 10,
        "only_bound": True,
        "ha_url": "http://homeassistant:8123",
        "ha_token": "",
        "ha_notify_service": "notify",  # notify.notify => "notify"
    }
    try:
        with open(OPTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f) or {}
        defaults.update(data)
    except FileNotFoundError:
        # In some setups options might not exist yet; keep defaults.
        pass
    return defaults


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


def ha_notify(ha_url, ha_token, ha_notify_service, title, message):
    if not ha_token:
        print("ha_token missing; skipping notify")
        return

    ha_url = ha_url.rstrip("/")
    url = f"{ha_url}/api/services/notify/{ha_notify_service}"
    headers = {"Authorization": f"Bearer {ha_token}", "Content-Type": "application/json"}
    payload = {"title": title, "message": message}

    r = requests.post(url, headers=headers, json=payload, timeout=10)
    if r.status_code >= 300:
        print(f"Notify failed: {r.status_code} {r.text}")
    else:
        print("Notify sent")


def normalize_lease(l):
    return {
        "address": l.get("address", ""),
        "mac": l.get("mac-address", ""),
        "host": l.get("host-name", ""),
        "server": l.get("server", ""),
        "status": l.get("status", ""),
    }


def connect(opts):
    host = opts["mikrotik_host"]
    user = opts["mikrotik_user"]
    password = opts["mikrotik_password"]
    port = int(opts["mikrotik_port"])
    use_ssl = bool(opts["mikrotik_use_ssl"])

    if not host or not user or not password:
        raise RuntimeError("Missing MikroTik credentials/host in options.json")

    pool = RouterOsApiPool(
        host,
        username=user,
        password=password,
        port=port,
        use_ssl=use_ssl,
        ssl_verify=False,
        plaintext_login=True,
    )
    return pool


def main():
    opts = load_options()
    state = load_state()
    seen_macs = set(m.lower() for m in state.get("seen_macs", []) if isinstance(m, str))

    poll_seconds = int(opts["poll_seconds"])
    only_bound = bool(opts["only_bound"])

    print("Starting MikroTik DHCP lease watcher (options.json mode)")
    print(
        f"MikroTik={opts['mikrotik_host']}:{opts['mikrotik_port']} SSL={opts['mikrotik_use_ssl']} "
        f"POLL={poll_seconds}s ONLY_BOUND={only_bound} OPTIONS_FILE={OPTIONS_FILE}"
    )

    pool = None
    api = None

    while True:
        try:
            # Reload options occasionally if you change add-on config without restart.
            # (cheap and safe)
            opts = load_options()
            poll_seconds = int(opts["poll_seconds"])
            only_bound = bool(opts["only_bound"])

            if pool is None:
                pool = connect(opts)
                api = pool.get_api()

            leases = api.get_resource("/ip/dhcp-server/lease").get()

            new_items = []
            for raw in leases:
                lease = normalize_lease(raw)

                if only_bound and lease["status"] != "bound":
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
                    ha_notify(
                        opts["ha_url"],
                        opts["ha_token"],
                        opts["ha_notify_service"],
                        title,
                        msg,
                    )

            time.sleep(poll_seconds)

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
