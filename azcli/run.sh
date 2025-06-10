#!/usr/bin/env bash
set -e

echo "Starting Azure CLI Add-on..."

TENANT_ID=$(bashio::config 'tenant_id')
CLIENT_ID=$(bashio::config 'client_id')
CLIENT_SECRET=$(bashio::config 'client_secret')

bashio::log.info "Tenant ID: ${TENANT_ID}"
bashio::log.info "Client ID: ${CLIENT_ID}"
bashio::log.info "Client Secret: ${CLIENT_SECRET}"

# Login with Service Principal using env vars from config.json
#az login --service-principal --username "$CLIENT_ID" --password "$CLIENT_SECRET" --tenant "$TENANT_ID"
#az account list --output table || echo "You may need to login using a service principal."
#echo "Logged in as Service Principal, ready for commands."

# Keep running to keep container alive
tail -f /dev/null