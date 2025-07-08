# 🧩 Home Assistant OS Add-ons by @dx

This repository contains custom add-ons for [Home Assistant OS](https://www.home-assistant.io/installation/). These tools extend the capabilities of your HA instance by integrating with cloud services, managing backups, and offering useful system utilities.

📦 All add-ons are built for **Home Assistant OS** and designed to run in lightweight Alpine- or Debian-based containers.

---

## 📁 Add-ons Included

### 🔹 [MariaDB Backup](https://github.com/dimxyp/haos_addons/tree/main/mariadbbackup)

Create manual or scheduled `.sql` dumps of your MariaDB `homeassistant` database. Useful for maintaining regular backups.

- Dumps stored in `/shared/`
- Reads DB credentials from configuration
- Output: `mariadb_backup_<date>.sql`

🔗 [README](https://github.com/dimxyp/haos_addons/blob/main/mariadbbackup/README.md)

---

### 🔹 [Azure CLI (azcli)](https://github.com/dimxyp/haos_addons/tree/main/azcli)

Run Azure CLI (`az`) commands from within Home Assistant.

- Authenticate with a service principal or device login
- Schedule scripts or call via automations
- Based on official `mcr.microsoft.com/azure-cli`

🔗 [README](https://github.com/dimxyp/haos_addons/blob/main/azcli/README.md)

---

### 🔹 [Azure REST CLI (azrestcli)](https://github.com/dimxyp/haos_addons/tree/main/azrestcli)

Low-level add-on to execute raw Azure REST API requests (using `curl` with bearer token). Ideal for calling Azure endpoints not covered by `azcli`.

- Uses `curl` + token file
- Works with ARM, MS Graph, AVD, etc.
- Easy automation integration

🔗 [README](https://github.com/dimxyp/haos_addons/blob/main/azrestcli/README.md)

---

### 🔹 [yt-dlp YouTube Downloader/Streamer](https://github.com/dimxyp/haos_addons/tree/main/ytdlp)

Download or stream YouTube videos or audio files via Home Assistant:

- `video` or `audio` → download to `/media`
- `stream` → play directly on a `media_player` (e.g., Nest Mini)
- Controlled via `rest_command` and `shell_command`

🔗 [README](https://github.com/dimxyp/haos_addons/blob/main/ytdlp/README.md)

---

