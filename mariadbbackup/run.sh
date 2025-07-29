#!/usr/bin/env bash
set -e

CONFIG_PATH="/data/options.json"

echo "[INFO] Loading configuration..."

DB_HOST=$(jq --raw-output '.DB_HOST // "core-mariadb"' "$CONFIG_PATH")
DB_USER=$(jq --raw-output '.DB_USER // "homeassistant"' "$CONFIG_PATH")
DB_PASS=$(jq --raw-output '.DB_PASS // empty' "$CONFIG_PATH")
DB_BACKUPDIR=$(jq --raw-output '.DB_BACKUPDIR // "/share/DBbackups"' "$CONFIG_PATH")
DB_RETENTION_DAYS=$(jq --raw-output '.DB_RETENTION_DAYS // 60' "$CONFIG_PATH")

OUTPUT_FOLDER="$DB_BACKUPDIR"

# Date and time
TODAY=$(date +"%Y%m%d")
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
TIMESTP_LOG=$(date +"%Y%m%d%H%M")

ARCHIVE_FOLDER="$OUTPUT_FOLDER/$TODAY"
ARCHIVE_FILE="$ARCHIVE_FOLDER/backup_${TODAY}.tar.gz"

echo "$TIMESTP_LOG [INFO] Starting MariaDB dump process..."

# Housekeeping: Archive previous .sql files if any
SQL_FILES=$(find "$OUTPUT_FOLDER" -maxdepth 1 -type f -name '*.sql')

if [ -n "$SQL_FILES" ]; then
  echo "$TIMESTP_LOG [INFO] Archiving old backups into $ARCHIVE_FILE ..."
  mkdir -p "$ARCHIVE_FOLDER"
  
  # Use tar with full file paths
  tar -czf "$ARCHIVE_FILE" -C "$OUTPUT_FOLDER" $(basename -a $SQL_FILES)

  echo "$TIMESTP_LOG [INFO] Removing old .sql files from $OUTPUT_FOLDER ..."
  rm -f $SQL_FILES
else
  echo "$TIMESTP_LOG [INFO] No previous SQL backup files found to archive."
fi

# Get the list of databases
DATABASES=$(mariadb --skip-ssl -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" -e "SHOW DATABASES;" | tail -n +2)

for DB in $DATABASES; do
  # Skip system databases
  if [[ "$DB" == "information_schema" || "$DB" == "performance_schema" || "$DB" == "mysql" || "$DB" == "sys" ]]; then
    echo "$TIMESTP_LOG [INFO] Skipping system database: $DB"
    continue
  fi

  OUTPUT_FILE="$OUTPUT_FOLDER/${DB}_backup_$TIMESTAMP.sql"
  echo "$TIMESTP_LOG [INFO] Backing up database: $DB → $OUTPUT_FILE"
  
  if mariadb-dump --skip-ssl -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB" > "$OUTPUT_FILE"; then
    echo "$TIMESTP_LOG [SUCCESS] Database $DB backed up successfully."
  else
    echo "$TIMESTP_LOG [ERROR] Failed to back up database $DB."
    rm -f "$OUTPUT_FILE"
  fi
done

# Housekeeping: Delete folders older than two months
echo "$TIMESTP_LOG [INFO] Performing housekeeping to delete folders older than selected days..."
find "$OUTPUT_FOLDER" -type d -mtime +$DB_RETENTION_DAYS -exec rm -rf {} +

echo "$TIMESTP_LOG [INFO] Backup process completed."
