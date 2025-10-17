# Local Development Setup

This document explains how local development authentication works for this Azure Functions project.

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
