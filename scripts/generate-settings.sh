#!/bin/bash

# Get values from azd environment
echo "Getting environment values from azd..."
COSMOS_ENDPOINT=$(azd env get-values | grep COSMOS_ENDPOINT | cut -d'"' -f2)
AZURE_OPENAI_ENDPOINT=$(azd env get-values | grep AZURE_OPENAI_ENDPOINT | cut -d'"' -f2)
AZUREWEBJOBSSTORAGE=$(azd env get-values | grep AZUREWEBJOBSSTORAGE | cut -d'"' -f2)

# Create or update local.settings.json
echo "Generating local.settings.json in src directory..."
cat > src/local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsSecretStorageType": "files",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PYTHON_ENABLE_WORKER_EXTENSIONS": "True",
    "COSMOS_DATABASE_NAME": "dev-snippet-db",
    "COSMOS_CONTAINER_NAME": "code-snippets",
    "BLOB_CONTAINER_NAME": "snippet-backups",
    "EMBEDDING_MODEL_DEPLOYMENT_NAME": "text-embedding-3-small",
    "AGENTS_MODEL_DEPLOYMENT_NAME": "gpt-4o-mini",
    "COSMOS_ENDPOINT": "$COSMOS_ENDPOINT",
    "AZURE_OPENAI_ENDPOINT": "$AZURE_OPENAI_ENDPOINT"
  }
}
EOF

echo ""
echo "✅ local.settings.json generated successfully!"
echo ""
echo "📝 Note: This configuration uses Azure credential authentication (no API key)."
echo "   - Make sure you're logged in: az login"
echo "   - You should have been automatically assigned the 'Cognitive Services OpenAI User' role"
echo "   - If you get authentication errors, verify your role assignment in the Azure Portal"