# 🗄️ MariaDB Backup Add-on for Home Assistant OS

This is a Home Assistant OS-compatible add-on that creates scheduled and manual backups of Home Assistant MariaDB database.

It uses `mariadb-dump` to export the database and stores the result as a timestamped `.sql` file in the `/share` directory.

---

## 🔧 How It Works

The `run.sh` script:

1. Connects to the running MariaDB container used by Home Assistant.
2. Runs a `mariadb-dump` of all databases using credentials stored in `/data/secrets.txt`.
3. Saves the `.sql` backup file to `/share/DBbackups/mariadb_backup_<DATE>.sql`.  # I know this need change to use variable location :P

---

## 🔐 Credentials

You must provide database credentials in the add-on configuration:

```json
{
  "host": "core-mariadb",   # your HA MariaDB - https://github.com/home-assistant/addons/tree/master/mariadb
  "port": 3306,
  "username": "homeassistant",
  "password": "YOUR_DB_PASSWORD"
}
```

🚀 Manual Backup

You can trigger a manual backup by restarting the add-on or calling the script from the container:

```
bash /run.sh
```
📅 Scheduled Backups using HA Automation


```
alias: MariaDBBackup
description: ""
triggers:
  - at: "23:00:00"
    enabled: true
    trigger: time
conditions:
  - condition: time
    weekday:
      - sun
actions:
  - action: hassio.addon_start
    data:
      addon: 00000XX_mariadb-backup # name of mariadbbackup 
mode: single
```

📦 Output
Backups are saved under:

```
/share/DBbackups/mariadb_backup_YYYY-MM-DD_HH-MM-SS.sql
```

🛠️ Dependencies
- mariadb-client
- bash
- core-mariadb add-on must be running and accessible



✍️ Author
Made with 💙 by @dimx
