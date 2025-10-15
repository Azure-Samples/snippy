# PowerShell script to generate local.settings.json

# Get values from azd environment
Write-Host "Getting environment values from azd..."
$azdValues = azd env get-values
$COSMOS_ENDPOINT = ($azdValues | Select-String 'COSMOS_ENDPOINT="(.*?)"').Matches.Groups[1].Value
$PROJECT_CONNECTION_STRING = ($azdValues | Select-String 'PROJECT_CONNECTION_STRING="(.*?)"').Matches.Groups[1].Value
$AZURE_OPENAI_ENDPOINT = ($azdValues | Select-String 'AZURE_OPENAI_ENDPOINT="(.*?)"').Matches.Groups[1].Value
$AZURE_OPENAI_KEY = ($azdValues | Select-String 'AZURE_OPENAI_KEY="(.*?)"').Matches.Groups[1].Value
$AZUREWEBJOBSSTORAGE = ($azdValues | Select-String 'AZUREWEBJOBSSTORAGE="(.*?)"').Matches.Groups[1].Value

# Create the JSON content
$jsonContent = @"
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
"@

# Write content to local.settings.json
$settingsPath = Join-Path (Get-Location) "src" "local.settings.json"
$jsonContent | Out-File -FilePath $settingsPath -Encoding utf8

Write-Host "local.settings.json generated successfully in src directory!"