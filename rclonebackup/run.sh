#!/usr/bin/env bash
set -e

CONFIG_PATH="/data/options.json"
RCLONE_CONF="/data/rclone.conf"

STORAGE_PROVIDER=$(jq --raw-output '.storage_provider // "azureblob"' "$CONFIG_PATH")
AZURE_ACCOUNT_NAME=$(jq --raw-output '.azure_account_name // empty' "$CONFIG_PATH")
AZURE_ACCOUNT_KEY=$(jq --raw-output '.azure_account_key // empty' "$CONFIG_PATH")
AZURE_SAS_URL=$(jq --raw-output '.azure_sas_url // empty' "$CONFIG_PATH")
AZURE_CONTAINER=$(jq --raw-output '.azure_container // empty' "$CONFIG_PATH")
REMOTE_SUBPATH=$(jq --raw-output '.remote_subpath // empty' "$CONFIG_PATH")
MOUNT_PATH=$(jq --raw-output '.mount_path // "/share/cloud"' "$CONFIG_PATH")
VFS_CACHE_MODE=$(jq --raw-output '.vfs_cache_mode // "writes"' "$CONFIG_PATH")
EXTRA_CONFIG=$(jq --raw-output '.extra_rclone_config // empty' "$CONFIG_PATH")

if [ "$STORAGE_PROVIDER" = "custom" ] && [ -n "$EXTRA_CONFIG" ]; then
  printf '%s\n' "$EXTRA_CONFIG" > "$RCLONE_CONF"
else
  {
    echo "[remote]"
    echo "type = azureblob"
    [ -n "$AZURE_ACCOUNT_NAME" ] && echo "account = $AZURE_ACCOUNT_NAME"
    if [ -n "$AZURE_SAS_URL" ]; then
      echo "sas_url = $AZURE_SAS_URL"
    elif [ -n "$AZURE_ACCOUNT_KEY" ]; then
      echo "key = $AZURE_ACCOUNT_KEY"
    fi
  } > "$RCLONE_CONF"
fi

REMOTE_TARGET="remote:${AZURE_CONTAINER}/${REMOTE_SUBPATH}"
REMOTE_TARGET="${REMOTE_TARGET%/}"

mkdir -p "$MOUNT_PATH"
fusermount -uz "$MOUNT_PATH" 2>/dev/null || true

cleanup() {
  fusermount -uz "$MOUNT_PATH" 2>/dev/null || true
  exit 0
}
trap cleanup TERM INT

echo "[INFO] Mounting ${REMOTE_TARGET} to ${MOUNT_PATH}"

exec rclone mount "$REMOTE_TARGET" "$MOUNT_PATH" \
  --config "$RCLONE_CONF" \
  --allow-other \
  --vfs-cache-mode "$VFS_CACHE_MODE" \
  --dir-cache-time 72h \
  --log-level INFO
