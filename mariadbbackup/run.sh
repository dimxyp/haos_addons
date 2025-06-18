#!/usr/bin/env bash
set -e
echo "[INFO] Starting MySQL dump process..."

CONFIG_PATH="/data/options.json"

# These values can be modified if you have different credentials
#DB_HOST="core-mariadb"
#DB_USER="homeassistant"
#DB_PASS=$(cat /data/.secret_mariadb | tr -d '\n')

DB_HOST=$(jq --raw-output '.DB_HOST // empty' $CONFIG_PATH)
DB_USER=$(jq --raw-output '.DB_USER // empty' $CONFIG_PATH)
DB_PASS=$(jq --raw-output '.DB_PASS // empty' $CONFIG_PATH)

# Output folder passed from config
OUTPUT_FOLDER="/share/sqlbackups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_FILE="$OUTPUT_FOLDER/mariadb_backup_$TIMESTAMP.sql"

mkdir -p "$OUTPUT_FOLDER"

echo "[INFO] Dumping all databases to $OUTPUT_FILE..."
mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" --all-databases > "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
  echo "[SUCCESS] Backup completed successfully."
else
  echo "[ERROR] Backup failed!"
  exit 1
fi
