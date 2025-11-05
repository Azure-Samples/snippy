#!/usr/bin/env pwsh

# Get subscription ID
$subscriptionId = (az account show --query id -o tsv)

# Get tenant ID
$tenantId = (az account show --query tenantId -o tsv)

# Get environment name from azd
$envName = (azd env get-value AZURE_ENV_NAME)
if (-not $envName) {
    Write-Error "Error: AZURE_ENV_NAME not found in azd environment"
    exit 1
}

# Construct resource group name (follows azd naming convention)
$resourceGroup = "rg-$envName"

# Get function app name from azd
$functionName = (azd env get-value AZURE_FUNCTION_NAME)
if (-not $functionName) {
    Write-Error "Error: AZURE_FUNCTION_NAME not found in azd environment"
    exit 1
}

# Get DTS scheduler name
$dtsName = (az resource list --resource-group $resourceGroup --resource-type "Microsoft.DurableTask/schedulers" --query "[0].name" -o tsv)
if (-not $dtsName) {
    Write-Error "Error: No DTS scheduler found in resource group $resourceGroup"
    exit 1
}

# Get DTS endpoint
$dtsEndpoint = (az resource show --resource-group $resourceGroup --name $dtsName --resource-type "Microsoft.DurableTask/schedulers" --query "properties.endpoint" -o tsv)

# Get task hub name from function app settings
$taskHubName = (az functionapp config appsettings list --name $functionName --resource-group $resourceGroup --query "[?name=='TASKHUB_NAME'].value" -o tsv)
if (-not $taskHubName) {
    Write-Error "Error: TASKHUB_NAME not found in function app settings"
    exit 1
}

# URL encode the endpoint
$encodedEndpoint = [System.Web.HttpUtility]::UrlEncode($dtsEndpoint.Trim())

# Construct the full dashboard URL
$dashboardUrl = "https://dashboard.durabletask.io/subscriptions/$subscriptionId/schedulers/$dtsName/taskhubs/${taskHubName}?endpoint=$encodedEndpoint&tenantId=$tenantId"

Write-Output $dashboardUrl
