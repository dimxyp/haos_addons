#!/usr/bin/env bash
set -e

echo "Starting Azure CLI Add-on version 1.1.3 ..."

CONFIG_PATH="/data/options.json"

TENANT_ID=$(jq --raw-output '.tenant_id // empty' $CONFIG_PATH)
CLIENT_ID=$(jq --raw-output '.client_id // empty' $CONFIG_PATH)
CLIENT_SECRET=$(jq --raw-output '.client_secret // empty' $CONFIG_PATH)

# echo "Tenant ID: ${TENANT_ID}"
# echo "Client ID: ${CLIENT_ID}"
# echo "Client Secret: ${CLIENT_SECRET}"

# Login with Service Principal using env vars from config.json
az login --service-principal --username "$CLIENT_ID" --password "$CLIENT_SECRET" --tenant "$TENANT_ID"
az account list --output table || echo "You may need to login using a service principal."

while true; do
    echo "Waiting for Azure CLI command..."
    nc -l -p 5902 | while read command; do
        echo "Executing: $command"
        eval "$command"
    done
done
# Keep running to keep container alive
#tail -f /dev/null