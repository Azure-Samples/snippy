#!/bin/bash

# Get values from azd environment
echo "Getting environment values from azd..."
COSMOS_ENDPOINT=$(azd env get-values | grep COSMOS_ENDPOINT | cut -d'"' -f2)
AZURE_OPENAI_ENDPOINT=$(azd env get-values | grep AZURE_OPENAI_ENDPOINT | cut -d'"' -f2)
PROJECT_ENDPOINT=$(azd env get-values | grep PROJECT_ENDPOINT | cut -d'"' -f2)
AZUREWEBJOBSSTORAGE=$(azd env get-values | grep AZUREWEBJOBSSTORAGE | cut -d'"' -f2)
DTS_URL=$(azd env get-values | grep DTS_URL | cut -d'"' -f2)
TASKHUB_NAME=$(azd env get-values | grep TASKHUB_NAME | cut -d'"' -f2)

# Create or update local.settings.json
echo "Generating local.settings.json in src directory..."
cat > src/local.settings.json << EOF
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "AzureWebJobsSecretStorageType": "files",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "PYTHON_ENABLE_WORKER_EXTENSIONS": "True",
    "DTS_CONNECTION_STRING": "Endpoint=http://localhost:8080;Authentication=None",
    "TASKHUB_NAME": "default",
    "COSMOS_DATABASE_NAME": "dev-snippet-db",
    "COSMOS_CONTAINER_NAME": "code-snippets",
    "BLOB_CONTAINER_NAME": "snippet-backups",
    "EMBEDDING_MODEL_DEPLOYMENT_NAME": "text-embedding-3-small",
    "AGENTS_MODEL_DEPLOYMENT_NAME": "gpt-4o-mini",
    "COSMOS_ENDPOINT": "$COSMOS_ENDPOINT",
    "AZURE_OPENAI_ENDPOINT": "$AZURE_OPENAI_ENDPOINT",
    "PROJECT_ENDPOINT": "$PROJECT_ENDPOINT",
    "PYTHON_ISOLATE_WORKER_DEPENDENCIES": "1"
  }
}
EOF

echo ""
echo "✅ local.settings.json generated successfully!"
echo ""
echo "📝 Note: This configuration uses:"
echo "   - Durable Task Scheduler emulator at http://localhost:8080"
echo "   - Azure credential authentication for Azure services (no API key)"
echo "   - Make sure you're logged in: az login"
echo "   - You should have been automatically assigned the 'Cognitive Services OpenAI User' role"
echo ""
echo "🐳 Before running 'func start', start the DTS emulator:"
echo "   docker compose up -d"
echo "   # Or manually: docker run -d -p 8080:8080 -p 8082:8082 mcr.microsoft.com/dts/dts-emulator:latest"
echo ""
echo "📊 DTS Dashboard will be available at: http://localhost:8082/"