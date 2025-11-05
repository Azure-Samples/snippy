#!/bin/bash
set -e

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)

# Get tenant ID  
TENANT_ID=$(az account show --query tenantId -o tsv)

# Get environment name from azd
ENV_NAME=$(azd env get-value AZURE_ENV_NAME 2>/dev/null)
if [ -z "$ENV_NAME" ]; then
    echo "Error: AZURE_ENV_NAME not found in azd environment" >&2
    exit 1
fi

# Construct resource group name (follows azd naming convention)
RESOURCE_GROUP="rg-${ENV_NAME}"

# Get function app name from azd
FUNCTION_NAME=$(azd env get-value AZURE_FUNCTION_NAME 2>/dev/null)
if [ -z "$FUNCTION_NAME" ]; then
    echo "Error: AZURE_FUNCTION_NAME not found in azd environment" >&2
    exit 1
fi

# Get DTS scheduler name
DTS_NAME=$(az resource list --resource-group "$RESOURCE_GROUP" --resource-type "Microsoft.DurableTask/schedulers" --query "[0].name" -o tsv)
if [ -z "$DTS_NAME" ]; then
    echo "Error: No DTS scheduler found in resource group $RESOURCE_GROUP" >&2
    exit 1
fi

# Get DTS endpoint
DTS_ENDPOINT=$(az resource show --resource-group "$RESOURCE_GROUP" --name "$DTS_NAME" --resource-type "Microsoft.DurableTask/schedulers" --query "properties.endpoint" -o tsv)

# Get task hub name from function app settings
TASKHUB_NAME=$(az functionapp config appsettings list --name "$FUNCTION_NAME" --resource-group "$RESOURCE_GROUP" --query "[?name=='TASKHUB_NAME'].value" -o tsv)
if [ -z "$TASKHUB_NAME" ]; then
    echo "Error: TASKHUB_NAME not found in function app settings" >&2
    exit 1
fi

# URL encode the endpoint (remove any trailing newlines first)
ENCODED_ENDPOINT=$(echo -n $DTS_ENDPOINT | jq -sRr @uri)

# Construct the full dashboard URL
DASHBOARD_URL="https://dashboard.durabletask.io/subscriptions/${SUBSCRIPTION_ID}/schedulers/${DTS_NAME}/taskhubs/${TASKHUB_NAME}?endpoint=${ENCODED_ENDPOINT}&tenantId=${TENANT_ID}"

echo $DASHBOARD_URL
