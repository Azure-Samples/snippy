# PowerShell script to generate local.settings.json

# Get values from azd environment
Write-Host "Getting environment values from azd..."
$envValues = azd env get-values | Out-String
$cosmosEndpoint = ($envValues | Select-String 'COSMOS_ENDPOINT="([^"]*)"').Matches.Groups[1].Value
$azureOpenAIEndpoint = ($envValues | Select-String 'AZURE_OPENAI_ENDPOINT="([^"]*)"').Matches.Groups[1].Value
$projectEndpoint = ($envValues | Select-String 'PROJECT_ENDPOINT="([^"]*)"').Matches.Groups[1].Value
$azureWebJobsStorage = ($envValues | Select-String 'AZUREWEBJOBSSTORAGE="([^"]*)"').Matches.Groups[1].Value
$dtsUrl = ($envValues | Select-String 'DTS_URL="([^"]*)"').Matches.Groups[1].Value
$taskhubName = ($envValues | Select-String 'TASKHUB_NAME="([^"]*)"').Matches.Groups[1].Value

# Use default taskhub name if not found
if ([string]::IsNullOrEmpty($taskhubName)) {
    $taskhubName = "SnippyTaskHub"
}

# Create or update local.settings.json
Write-Host "Generating local.settings.json in src directory..."
$settingsJson = @"
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
    "COSMOS_ENDPOINT": "$cosmosEndpoint",
    "AZURE_OPENAI_ENDPOINT": "$azureOpenAIEndpoint",
    "PROJECT_ENDPOINT": "$projectEndpoint",
    "PYTHON_ISOLATE_WORKER_DEPENDENCIES": "1"
  }
}
"@

$settingsJson | Out-File -FilePath "src/local.settings.json" -Encoding utf8
Write-Host ""
Write-Host "✅ local.settings.json generated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Note: This configuration uses:" -ForegroundColor Cyan
Write-Host "   - Durable Task Scheduler emulator at http://localhost:8080" -ForegroundColor Cyan
Write-Host "   - Azure credential authentication for Azure services (no API key)" -ForegroundColor Cyan
Write-Host "   - Make sure you're logged in: az login" -ForegroundColor Cyan
Write-Host "   - You should have been automatically assigned the 'Cognitive Services OpenAI User' role" -ForegroundColor Cyan
Write-Host ""
Write-Host "🐳 Before running 'func start', start the DTS emulator:" -ForegroundColor Yellow
Write-Host "   docker compose up -d" -ForegroundColor Yellow
Write-Host "   # Or manually: docker run -d -p 8080:8080 -p 8082:8082 mcr.microsoft.com/dts/dts-emulator:latest" -ForegroundColor Yellow
Write-Host ""
Write-Host "📊 DTS Dashboard will be available at: http://localhost:8082/" -ForegroundColor Yellow