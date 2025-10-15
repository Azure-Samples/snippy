#!/bin/bash

# Get values from azd environment
echo "Getting environment values from azd..."
COSMOS_ENDPOINT=$(azd env get-values | grep COSMOS_ENDPOINT | cut -d'"' -f2)
PROJECT_CONNECTION_STRING=$(azd env get-values | grep PROJECT_CONNECTION_STRING | cut -d'"' -f2)
AZURE_OPENAI_ENDPOINT=$(azd env get-values | grep AZURE_OPENAI_ENDPOINT | cut -d'"' -f2)
AZURE_OPENAI_KEY=$(azd env get-values | grep AZURE_OPENAI_KEY | cut -d'"' -f2)
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
    "PROJECT_CONNECTION_STRING": "$PROJECT_CONNECTION_STRING",
    "AZURE_OPENAI_ENDPOINT": "$AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY": "$AZURE_OPENAI_KEY"
  }
}
EOF

echo "local.settings.json generated successfully in src directory!"