# PowerShell script to generate local.settings.json

# Get values from azd environment
Write-Host "Getting environment values from azd..."
$envValues = azd env get-values | Out-String
$cosmosEndpoint = ($envValues | Select-String 'COSMOS_ENDPOINT="([^"]*)"').Matches.Groups[1].Value
$azureOpenAIEndpoint = ($envValues | Select-String 'AZURE_OPENAI_ENDPOINT="([^"]*)"').Matches.Groups[1].Value
$azureWebJobsStorage = ($envValues | Select-String 'AZUREWEBJOBSSTORAGE="([^"]*)"').Matches.Groups[1].Value

# Create or update local.settings.json
Write-Host "Generating local.settings.json in src directory..."
$settingsJson = @"
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
    "COSMOS_ENDPOINT": "$cosmosEndpoint",
    "AZURE_OPENAI_ENDPOINT": "$azureOpenAIEndpoint"
  }
}
"@

$settingsJson | Out-File -FilePath "src/local.settings.json" -Encoding utf8
Write-Host ""
Write-Host "✅ local.settings.json generated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Note: This configuration uses Azure credential authentication (no API key)." -ForegroundColor Cyan
Write-Host "   - Make sure you're logged in: az login" -ForegroundColor Cyan
Write-Host "   - You should have been automatically assigned the 'Cognitive Services OpenAI User' role" -ForegroundColor Cyan
Write-Host "   - If you get authentication errors, verify your role assignment in the Azure Portal" -ForegroundColor Cyan