# Randomly select one of the allowed regions and set it as the default
# Run this script before 'azd provision' or 'azd up' to use a random region
# without being prompted. Otherwise, azd will prompt you to select a region.

$regions = @("westus2", "westus3", "eastus2", "northcentralus")
$selectedRegion = Get-Random -InputObject $regions

Write-Host "🎲 Randomly selected region: $selectedRegion" -ForegroundColor Green
azd env set AZURE_LOCATION $selectedRegion
Write-Host "✅ Region set. Run 'azd provision' to deploy without being prompted." -ForegroundColor Green
Write-Host "   To change: azd env set AZURE_LOCATION <region>" -ForegroundColor Gray
