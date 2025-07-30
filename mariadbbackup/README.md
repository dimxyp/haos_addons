# 🗄️ MariaDB Backup Add-on for Home Assistant OS

This is a Home Assistant OS-compatible add-on that creates scheduled and manual backups of Home Assistant MariaDB database.

It uses `mariadb-dump` to export the database and stores the result as a timestamped `.sql` file in the `/share` directory.

---

## 🔧 How It Works

The `run.sh` script:

1. Connects to the running MariaDB container used by Home Assistant.
2. Runs a `mariadb-dump` of all databases using credentials stored in `/data/secrets.txt`.
3. Saves the `.sql` backup file to custom location.

---

## 🔐 Credentials

You must provide database credentials and backup location in the add-on configuration:

## ⚙️ Comfiguration 

```json
{
  "DB_HOST": "core-mariadb"   # your HA MariaDB - https://github.com/home-assistant/addons/tree/master/mariadb
  "DB_USER": "homeassistant"
  "DB_PASS": "YOUR_DB_PASSWORD"
  "DB_BACKUPDIR": "/share/... /config/... or any other"
  "DB_RETENTION_DAYS": "days of housekeeping retention"
}
```

🚀 Manual Backup

You can trigger a manual backup by starting the add-on.


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
$DB_BACKUPDIR/mariadb_backup_YYYY-MM-DD_HH-MM-SS.sql
```

🛠️ Dependencies
- core-mariadb add-on must be running and accessible
- creds
- backup location
- retention period



✍️ Author
Made with 💙 by @dimx
