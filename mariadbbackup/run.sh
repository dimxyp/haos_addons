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
OUTPUT_FOLDER="/share/DBbackups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$OUTPUT_FOLDER"

# Get the list of databases
DATABASES=$(mariadb --skip-ssl -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "SHOW DATABASES;" | tail -n +2)

for DB in $DATABASES; do
  # Skip internal system DBs if you want (optional)
  if [[ "$DB" == "information_schema" ]] || [[ "$DB" == "performance_schema" ]] || [[ "$DB" == "mysql" ]] || [[ "$DB" == "sys" ]]; then
    echo "[INFO] Skipping system database: $DB"
    continue
  fi

  OUTPUT_FILE="$OUTPUT_FOLDER/${DB}_backup_$TIMESTAMP.sql"
  echo "[INFO] Backing up database: $DB to $OUTPUT_FILE"
  mariadb-dump --skip-ssl -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB" > "$OUTPUT_FILE"

  if [ $? -eq 0 ]; then
    echo "[SUCCESS] Database $DB backed up successfully."
  else
    echo "[ERROR] Failed to backup database $DB."
  fi
done

echo "[INFO] All done."
