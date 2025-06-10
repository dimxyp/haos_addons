#!/usr/bin/env bash
set -e

echo "Starting Azure CLI Add-on..."

CONFIG_PATH="/data/options.json"

TENANT_ID=$(jq --raw-output '.tenant_id // empty' $CONFIG_PATH)
CLIENT_ID=$(jq --raw-output '.client_id // empty' $CONFIG_PATH)
CLIENT_SECRET=$(jq --raw-output '.client_secret // empty' $CONFIG_PATH)

# echo "Tenant ID: ${TENANT_ID}"
# echo "Client ID: ${CLIENT_ID}"
# echo "Client Secret: ${CLIENT_SECRET}"

CONFIG_PATH="/data/config.yaml"

if [ -f "$CONFIG_PATH" ]; then
    VERSION=$(grep '^version:' "$CONFIG_PATH" | awk '{print $2}')
    echo "Current AzureCLI Version: $VERSION"
else
    echo "config.yaml not found!"
fi

# Login with Service Principal using env vars from config.json
az login --service-principal --username "$CLIENT_ID" --password "$CLIENT_SECRET" --tenant "$TENANT_ID"
az account list --output table || echo "You may need to login using a service principal."

while true; do
    echo "Waiting for Azure CLI command..."
    nc -l -p 5902 -e /bin/bash -c 'read command; eval "$command"'
done
# Keep running to keep container alive
#tail -f /dev/null