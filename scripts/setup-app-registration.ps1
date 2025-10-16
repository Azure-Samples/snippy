# Pre-provision hook to create Azure AD App Registration and set azd environment variables
# This script runs automatically before 'azd provision'

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setting up Azure AD App Registration" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get environment name and location from azd first
$ENVIRONMENT_NAME = azd env get-value AZURE_ENV_NAME 2>$null
$LOCATION = azd env get-value AZURE_LOCATION 2>$null

if (-not $ENVIRONMENT_NAME -or -not $LOCATION) {
    Write-Host "❌ Error: AZURE_ENV_NAME or AZURE_LOCATION not set" -ForegroundColor Red
    Write-Host "   Please ensure azd environment is initialized"
    exit 1
}

# Check if we already have the app registration values in the environment
$EXISTING_CLIENT_ID = azd env get-value APP_REGISTRATION_CLIENT_ID 2>$null

# Only skip if we have a valid GUID (not empty string)
if ($EXISTING_CLIENT_ID -and $EXISTING_CLIENT_ID -match '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$') {
    # Get the display name from Azure to show user
    $EXISTING_NAME = az ad app show --id "$EXISTING_CLIENT_ID" --query "displayName" -o tsv 2>$null
    if (-not $EXISTING_NAME) { $EXISTING_NAME = "Unknown" }
    Write-Host "✓ App registration already configured:" -ForegroundColor Green
    Write-Host "  Display Name: $EXISTING_NAME"
    Write-Host "  Client ID: $EXISTING_CLIENT_ID"
    Write-Host "  Skipping app registration creation."
    Write-Host ""
    exit 0
}

Write-Host "Environment: $ENVIRONMENT_NAME"
Write-Host "Location: $LOCATION"
Write-Host ""

# Get subscription ID
$SUBSCRIPTION_ID = az account show --query id -o tsv 2>$null
if (-not $SUBSCRIPTION_ID) {
    Write-Host "❌ Error: Not logged into Azure CLI" -ForegroundColor Red
    Write-Host "   Please run: az login"
    exit 1
}

# Generate resource token using MD5 hash for consistency
$hashInput = "${SUBSCRIPTION_ID}-${ENVIRONMENT_NAME}-${LOCATION}"
$md5 = [System.Security.Cryptography.MD5]::Create()
$hash = $md5.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($hashInput))
$RESOURCE_TOKEN = ([System.BitConverter]::ToString($hash) -replace '-','').Substring(0,13).ToLower()

# Variables
$APP_DISPLAY_NAME = "snippy-mcp-server-$RESOURCE_TOKEN"
$AUTHORIZED_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
$SCOPE_NAME = "access_as_user"

Write-Host "Environment: $ENVIRONMENT_NAME"
Write-Host "Resource Token: $RESOURCE_TOKEN"
Write-Host "App Display Name: $APP_DISPLAY_NAME"
Write-Host ""

Write-Host "Creating Azure AD App Registration for MCP Server..."
Write-Host ""

# Ensure user is logged into Azure CLI
try {
    az account show | Out-Null
} catch {
    Write-Host "❌ Error: Not logged into Azure CLI" -ForegroundColor Red
    Write-Host "   Please run: az login"
    exit 1
}

# Check if app already exists by display name
$EXISTING_APP = az ad app list --display-name "$APP_DISPLAY_NAME" --query "[0].appId" -o tsv 2>$null
if ($EXISTING_APP) {
    Write-Host "✓ Found existing app registration: $EXISTING_APP" -ForegroundColor Green
    $APP_ID = $EXISTING_APP
    $OBJECT_ID = az ad app show --id $APP_ID --query "id" -o tsv
    $SCOPE_ID = az ad app show --id $APP_ID --query "api.oauth2PermissionScopes[0].id" -o tsv 2>$null
    
    # If scope doesn't exist, we need to create it
    if (-not $SCOPE_ID) {
        Write-Host "  Adding missing OAuth2 scope..."
        $SCOPE_ID = [guid]::NewGuid().ToString()
        
        # Step 1: Create the OAuth2 permission scope first
        $scopeBody = @"
{
  "api": {
    "oauth2PermissionScopes": [{
      "id": "$SCOPE_ID",
      "adminConsentDescription": "Allow the application to access the MCP server on your behalf",
      "adminConsentDisplayName": "Access to Snippy MCP Server",
      "userConsentDescription": "Allow the application to access the MCP server on your behalf",
      "userConsentDisplayName": "Access to Snippy MCP Server",
      "value": "$SCOPE_NAME",
      "type": "User",
      "isEnabled": true
    }]
  }
}
"@
        
        az rest --method PATCH `
            --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" `
            --headers "Content-Type=application/json" `
            --body $scopeBody | Out-Null
        
        # Step 2: Add the pre-authorized application
        $preAuthBody = @"
{
  "api": {
    "preAuthorizedApplications": [{
      "appId": "$AUTHORIZED_CLIENT_ID",
      "delegatedPermissionIds": ["$SCOPE_ID"]
    }]
  }
}
"@
        
        az rest --method PATCH `
            --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" `
            --headers "Content-Type=application/json" `
            --body $preAuthBody | Out-Null
        
        Write-Host "  ✓ OAuth2 scope configured" -ForegroundColor Green
    }
} else {
    Write-Host "Creating new app registration..."
    
    # Create the app registration
    $APP_JSON = az ad app create `
        --display-name "$APP_DISPLAY_NAME" `
        --sign-in-audience AzureADMyOrg `
        --query "{appId: appId, id: id}" -o json | ConvertFrom-Json
    
    $APP_ID = $APP_JSON.appId
    $OBJECT_ID = $APP_JSON.id
    
    Write-Host "  ✓ Created app: $APP_ID" -ForegroundColor Green
    
    # Set the application ID URI
    az ad app update --id $APP_ID --identifier-uris "api://$APP_ID"
    Write-Host "  ✓ Set Application ID URI: api://$APP_ID" -ForegroundColor Green
    
    # Generate a unique GUID for the scope
    $SCOPE_ID = [guid]::NewGuid().ToString()
    
    # Step 1: Create the OAuth2 permission scope first
    $scopeBody = @"
{
  "api": {
    "oauth2PermissionScopes": [{
      "id": "$SCOPE_ID",
      "adminConsentDescription": "Allow the application to access the MCP server on your behalf",
      "adminConsentDisplayName": "Access to Snippy MCP Server",
      "userConsentDescription": "Allow the application to access the MCP server on your behalf",
      "userConsentDisplayName": "Access to Snippy MCP Server",
      "value": "$SCOPE_NAME",
      "type": "User",
      "isEnabled": true
    }]
  }
}
"@
    
    az rest --method PATCH `
        --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" `
        --headers "Content-Type=application/json" `
        --body $scopeBody | Out-Null
    
    Write-Host "  ✓ Added OAuth2 scope: $SCOPE_NAME" -ForegroundColor Green
    
    # Step 2: Add the pre-authorized application
    $preAuthBody = @"
{
  "api": {
    "preAuthorizedApplications": [{
      "appId": "$AUTHORIZED_CLIENT_ID",
      "delegatedPermissionIds": ["$SCOPE_ID"]
    }]
  }
}
"@
    
    az rest --method PATCH `
        --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" `
        --headers "Content-Type=application/json" `
        --body $preAuthBody | Out-Null
    
    Write-Host "  ✓ Pre-authorized client: $AUTHORIZED_CLIENT_ID" -ForegroundColor Green
    
    # Create service principal if it doesn't exist
    $SP_ID = az ad sp create --id $APP_ID --query "id" -o tsv 2>$null
    if ($SP_ID) {
        Write-Host "  ✓ Created service principal" -ForegroundColor Green
    }
}

# Set azd environment variables
Write-Host ""
Write-Host "Configuring azd environment variables..."
azd env set APP_REGISTRATION_CLIENT_ID "$APP_ID"
azd env set APP_REGISTRATION_OBJECT_ID "$OBJECT_ID"
azd env set APP_REGISTRATION_SCOPE_ID "$SCOPE_ID"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ App Registration Setup Complete" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Application ID: $APP_ID"
Write-Host "Application ID URI: api://$APP_ID"
Write-Host "Scope ID: $SCOPE_ID"
Write-Host ""
Write-Host "Proceeding with infrastructure provisioning..."
Write-Host ""
