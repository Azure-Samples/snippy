#!/bin/bash
# Pre-provision hook to create Azure AD App Registration and set azd environment variables
# This script runs automatically before 'azd provision'

set -e

echo ""
echo "=========================================="
echo "Setting up Azure AD App Registration"
echo "=========================================="
echo ""

# Check if we already have the app registration values in the environment
EXISTING_CLIENT_ID=$(azd env get-value APP_REGISTRATION_CLIENT_ID 2>/dev/null || echo "")

# Only skip if we have a valid GUID (not empty string)
if [ -n "$EXISTING_CLIENT_ID" ] && [[ "$EXISTING_CLIENT_ID" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
  # Get the display name from Azure to show user
  EXISTING_NAME=$(az ad app show --id "$EXISTING_CLIENT_ID" --query "displayName" -o tsv 2>/dev/null || echo "Unknown")
  echo "✓ App registration already configured:"
  echo "  Display Name: $EXISTING_NAME"
  echo "  Client ID: $EXISTING_CLIENT_ID"
  echo "  Skipping app registration creation."
  echo ""
  exit 0
fi

# Get environment name and location from azd
ENVIRONMENT_NAME=$(azd env get-value AZURE_ENV_NAME 2>/dev/null || echo "")
LOCATION=$(azd env get-value AZURE_LOCATION 2>/dev/null || echo "")

if [ -z "$ENVIRONMENT_NAME" ] || [ -z "$LOCATION" ]; then
  echo "❌ Error: AZURE_ENV_NAME or AZURE_LOCATION not set"
  echo "   Please ensure azd environment is initialized"
  exit 1
fi

echo "Environment: $ENVIRONMENT_NAME"
echo "Location: $LOCATION"
echo ""

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv 2>/dev/null || echo "")
if [ -z "$SUBSCRIPTION_ID" ]; then
  echo "❌ Error: Not logged into Azure CLI"
  echo "   Please run: az login"
  exit 1
fi

# Generate resource token using a combination that should be reasonably unique
# This won't match Bicep's uniqueString() exactly, but will be consistent across runs
HASH_INPUT="${SUBSCRIPTION_ID}-${ENVIRONMENT_NAME}-${LOCATION}"
RESOURCE_TOKEN=$(echo -n "$HASH_INPUT" | md5sum | cut -c1-13 | tr '[:upper:]' '[:lower:]')

# Variables
APP_DISPLAY_NAME="snippy-mcp-server-${RESOURCE_TOKEN}"
AUTHORIZED_CLIENT_ID="04b07795-8ddb-461a-bbee-02f9e1bf7b46"
SCOPE_NAME="access_as_user"

echo "Resource Token: $RESOURCE_TOKEN"
echo "App Display Name: $APP_DISPLAY_NAME"
echo ""

echo "Creating Azure AD App Registration for MCP Server..."
echo ""

# Check if app already exists by display name
EXISTING_APP=$(az ad app list --display-name "$APP_DISPLAY_NAME" --query "[0].appId" -o tsv 2>/dev/null || echo "")

if [ -n "$EXISTING_APP" ]; then
  echo "✓ Found existing app registration: $EXISTING_APP"
  APP_ID=$EXISTING_APP
  OBJECT_ID=$(az ad app show --id $APP_ID --query "id" -o tsv)
  SCOPE_ID=$(az ad app show --id $APP_ID --query "api.oauth2PermissionScopes[0].id" -o tsv 2>/dev/null || echo "")
  
  # If scope doesn't exist, we need to create it
  if [ -z "$SCOPE_ID" ]; then
    echo "  Adding missing OAuth2 scope..."
    SCOPE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
    
    # Step 1: Create the OAuth2 permission scope first
    az rest --method PATCH \
      --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" \
      --headers "Content-Type=application/json" \
      --body "{
        \"api\": {
          \"oauth2PermissionScopes\": [{
            \"id\": \"$SCOPE_ID\",
            \"adminConsentDescription\": \"Allow the application to access the MCP server on your behalf\",
            \"adminConsentDisplayName\": \"Access to Snippy MCP Server\",
            \"userConsentDescription\": \"Allow the application to access the MCP server on your behalf\",
            \"userConsentDisplayName\": \"Access to Snippy MCP Server\",
            \"value\": \"$SCOPE_NAME\",
            \"type\": \"User\",
            \"isEnabled\": true
          }]
        }
      }" > /dev/null
    
    # Step 2: Add the pre-authorized application
    az rest --method PATCH \
      --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" \
      --headers "Content-Type=application/json" \
      --body "{
        \"api\": {
          \"preAuthorizedApplications\": [{
            \"appId\": \"$AUTHORIZED_CLIENT_ID\",
            \"delegatedPermissionIds\": [\"$SCOPE_ID\"]
          }]
        }
      }" > /dev/null
    
    echo "  ✓ OAuth2 scope configured"
  fi
else
  echo "Creating new app registration..."
  
  # Create the app registration
  APP_JSON=$(az ad app create \
    --display-name "$APP_DISPLAY_NAME" \
    --sign-in-audience AzureADMyOrg \
    --query "{appId: appId, id: id}" -o json)
  
  APP_ID=$(echo $APP_JSON | jq -r '.appId')
  OBJECT_ID=$(echo $APP_JSON | jq -r '.id')
  
  echo "  ✓ Created app: $APP_ID"
  
  # Set the application ID URI
  az ad app update --id $APP_ID --identifier-uris "api://$APP_ID"
  echo "  ✓ Set Application ID URI: api://$APP_ID"
  
  # Generate a unique GUID for the scope
  SCOPE_ID=$(uuidgen | tr '[:upper:]' '[:lower:]')
  
  # Step 1: Create the OAuth2 permission scope first
  az rest --method PATCH \
    --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" \
    --headers "Content-Type=application/json" \
    --body "{
      \"api\": {
        \"oauth2PermissionScopes\": [{
          \"id\": \"$SCOPE_ID\",
          \"adminConsentDescription\": \"Allow the application to access the MCP server on your behalf\",
          \"adminConsentDisplayName\": \"Access to Snippy MCP Server\",
          \"userConsentDescription\": \"Allow the application to access the MCP server on your behalf\",
          \"userConsentDisplayName\": \"Access to Snippy MCP Server\",
          \"value\": \"$SCOPE_NAME\",
          \"type\": \"User\",
          \"isEnabled\": true
        }]
      }
    }" > /dev/null
  
  echo "  ✓ Added OAuth2 scope: $SCOPE_NAME"
  
  # Step 2: Add the pre-authorized application
  az rest --method PATCH \
    --url "https://graph.microsoft.com/v1.0/applications/$OBJECT_ID" \
    --headers "Content-Type=application/json" \
    --body "{
      \"api\": {
        \"preAuthorizedApplications\": [{
          \"appId\": \"$AUTHORIZED_CLIENT_ID\",
          \"delegatedPermissionIds\": [\"$SCOPE_ID\"]
        }]
      }
    }" > /dev/null
  
  echo "  ✓ Pre-authorized client: $AUTHORIZED_CLIENT_ID"
  
  # Create service principal if it doesn't exist
  SP_ID=$(az ad sp create --id $APP_ID --query "id" -o tsv 2>/dev/null || echo "")
  if [ -n "$SP_ID" ]; then
    echo "  ✓ Created service principal"
  fi
fi

# Set azd environment variables
echo ""
echo "Configuring azd environment variables..."
azd env set APP_REGISTRATION_CLIENT_ID "$APP_ID"
azd env set APP_REGISTRATION_OBJECT_ID "$OBJECT_ID"
azd env set APP_REGISTRATION_SCOPE_ID "$SCOPE_ID"

echo ""
echo "=========================================="
echo "✅ App Registration Setup Complete"
echo "=========================================="
echo ""
echo "Application ID: $APP_ID"
echo "Application ID URI: api://$APP_ID"
echo "Scope ID: $SCOPE_ID"
echo ""
echo "Proceeding with infrastructure provisioning..."
echo ""
