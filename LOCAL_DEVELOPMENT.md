# Local Development Setup

This document explains how local development authentication works for this Azure Functions project.

## Quick Start

### Option A: With Docker (Recommended)

The fastest way to get started is using Docker Compose:

```bash
# Start both Azurite and DTS emulator
docker compose up -d

# Generate local settings from your Azure environment
./scripts/generate-settings.sh

# Run the Functions app
cd src
func start
```

**Dashboard URLs:**

- **Local DTS Dashboard**: <http://localhost:8082/> - Monitor orchestrations running locally
- **Azurite Blob**: <http://localhost:10000/>

**Monitoring Orchestrations:**

- **Local**: Open <http://localhost:8082/> to view orchestrations running against the local DTS emulator
- **Cloud**: Generate the Azure DTS dashboard URL with the provided scripts:

  ```bash
  ./scripts/get-dts-dashboard-url.sh
  ```
  or
  ```powershell
  .\scripts\get-dts-dashboard-url.ps1
  ```

  Then open the generated URL in your browser to view orchestrations running in Azure.

To stop the emulators:

```bash
docker compose down
```

### Option B: Without Docker - Native Azurite + Azure Storage Backend

If Docker is not available, you can use native Azurite and Azure Storage for Durable Functions:

```bash
# 1. Install Azurite globally via npm
npm install -g azurite

# 2. Start Azurite in a separate terminal
azurite

# 3. Temporarily switch to Azure Storage backend (see configuration below)

# 4. Generate local settings
./scripts/generate-settings.sh

# 5. Run the Functions app
cd src
func start
```

**Configuration changes for Azure Storage backend:**

Temporarily update `src/host.json` durableTask section:

```json
"durableTask": {
  "hubName": "%TASKHUB_NAME%",
  "storageProvider": {
    "type": "azureStorage",
    "connectionStringName": "AzureWebJobsStorage"
  },
  "tracing": {
    "traceInputsAndOutputs": true
  }
}
```

Your `local.settings.json` should have:

```json
{
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "TASKHUB_NAME": "default"
  }
}
```

**Note:** This approach uses Azure Storage (via Azurite) instead of DTS for orchestration state. You won't have the DTS dashboard, but all Durable Functions features will work.

### Switching Between Backends

Use the provided helper script to easily switch between DTS and Azure Storage:

```bash
# Switch to Azure Storage (for environments without Docker)
./scripts/switch-storage-backend.sh azureStorage

# Switch back to DTS (when Docker is available)
./scripts/switch-storage-backend.sh dts
```

PowerShell:

```powershell
# Switch to Azure Storage
.\scripts\switch-storage-backend.ps1 azureStorage

# Switch to DTS
.\scripts\switch-storage-backend.ps1 dts
```

The script automatically updates your `host.json` configuration and provides instructions for the required environment setup.

## Prerequisites

Before you begin, ensure you have:

1. **Docker** installed for running the Durable Task Scheduler emulator
2. **Azurite** installed for local Azure Storage emulation
3. **Azure CLI** installed and configured

## Durable Task Scheduler Setup

This project uses the **Durable Task Scheduler** (DTS) for orchestration instead of Azure Storage. For local development, you need to run the DTS emulator.

### 1. Start the DTS Emulator

Pull and run the DTS emulator Docker container:

```bash
# Pull the emulator image
docker pull mcr.microsoft.com/dts/dts-emulator:latest

# Run the emulator (exposes ports 8080 for gRPC and 8082 for dashboard)
docker run -d -p 8080:8080 -p 8082:8082 mcr.microsoft.com/dts/dts-emulator:latest
```

The emulator exposes two ports:
- **8080**: gRPC endpoint for the Functions app to connect
- **8082**: Dashboard UI at http://localhost:8082/

### 2. Start Azurite

The Azure Functions runtime still requires Azurite for some components:

```bash
azurite start
```

### 3. Verify Configuration

Check that your `local.settings.json` includes these DTS-specific settings:

```json
{
  "Values": {
    "DTS_CONNECTION_STRING": "Endpoint=http://localhost:8080;Authentication=None",
    "TASKHUB_NAME": "default"
  }
}
```

## Authentication Approach

This project uses **Azure Managed Identity** for authentication - both in production AND for local development. **No API keys are required!**

### How It Works

1. **In Azure (Production)**: The Function App uses its User-Assigned Managed Identity with the `Cognitive Services OpenAI User` role
2. **Locally**: Developers use their own Azure credentials via `az login` with the same role

## Setup Steps

### 1. Run `azd up` or `azd provision`

When you provision the infrastructure, the Bicep deployment automatically:
- Creates the Azure OpenAI resource
- Assigns the `Cognitive Services OpenAI User` role to the Function App's managed identity
- **Assigns the same role to YOU** (the person running `azd provision`)

This is done via the `principalId` parameter in `main.bicep`:

```bicep
// This assigns the role to the person running azd provision
module openaiRoleAssignmentDeveloper 'app/rbac/openai-access.bicep' = if (!empty(principalId)) {
  name: 'openaiRoleAssignmentDeveloper'
  scope: rg
  params: {
    openAIAccountName: openai.outputs.aiServicesName
    roleDefinitionId: CognitiveServicesOpenAIUser
    principalId: principalId  // Your user ID
  }
}
```

### 2. Make Sure You're Logged In

```bash
# Login to Azure
az login

# Verify you're using the correct subscription
az account show
```

### 3. Generate local.settings.json

```bash
# Run the postprovision script
./scripts/generate-settings.sh

# Verify it was created (notice: no API key!)
cat src/local.settings.json
```

### 4. Run the Function App Locally

```bash
cd src
func start
```

The Azure Functions runtime will automatically use your Azure credentials via `DefaultAzureCredential`.

### 5. Monitor Orchestrations

You can monitor orchestration instances in real-time using the DTS dashboard:

1. Open <http://localhost:8082/> in your browser
2. Click on your task hub (default: **default**)
3. View orchestration status, history, and execution details

**Note**: The DTS emulator stores data in memory, so all orchestration data is lost when the container stops.

## Benefits of This Approach

✅ **No secrets to manage** - No API keys in config files or environment variables  
✅ **More secure** - Credentials never leave Azure's identity system  
✅ **Production parity** - Local dev works exactly like production  
✅ **Automatic role assignment** - Developers get the right permissions when they provision  
✅ **Audit trail** - All API calls are tied to specific user identities

## Troubleshooting

### Error: "Access denied" or "Unauthorized"

1. **Check your Azure login**:
   ```bash
   az login
   az account show
   ```

2. **Verify your role assignment**:
   ```bash
   # Get your user principal ID
   az ad signed-in-user show --query id -o tsv
   
   # List role assignments (replace <resource-group> and <openai-name>)
   az role assignment list --assignee <your-principal-id> \
     --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<openai-name>
   ```

3. **If role is missing**, run `azd provision` again or manually assign:
   ```bash
   az role assignment create \
     --role "Cognitive Services OpenAI User" \
     --assignee <your-email-or-principal-id> \
     --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<openai-name>
   ```

### For Additional Developers

If other developers join the project:

**Option 1: They run `azd provision`** (if they have subscription permissions)
- This will automatically assign them the role

**Option 2: Manually assign the role** (if you're the admin)
```bash
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee <developer-email> \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<openai-name>
```

## FAQ

**Q: Do I need an API key for local development?**  
A: No! Just make sure you're logged in with `az login`.

**Q: What if I want to use an API key anyway?**  
A: You can manually add `AZURE_OPENAI_KEY` to your `local.settings.json`, but it's not recommended. The keyless approach is more secure.

**Q: Does this work in CI/CD pipelines?**  
A: Yes! Use a service principal or managed identity for your CI/CD pipeline with the same role assignment.

**Q: What about Cosmos DB access?**  
A: Same approach! Your user is assigned `DocumentDB Account Contributor` role during provisioning (see the `cosmosDb` module in `main.bicep`).
