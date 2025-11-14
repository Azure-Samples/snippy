#!/bin/bash
# Randomly select one of the allowed regions and set it as the default
# Run this script before 'azd provision' or 'azd up' to use a random region
# without being prompted. Otherwise, azd will prompt you to select a region.

REGIONS=("westus2" "westus3" "eastus2", "northcentralus")
RANDOM_INDEX=$((RANDOM % 3))
SELECTED_REGION="${REGIONS[$RANDOM_INDEX]}"

echo "🎲 Randomly selected region: $SELECTED_REGION"
azd env set AZURE_LOCATION "$SELECTED_REGION"
echo "✅ Region set. Run 'azd provision' to deploy without being prompted."
echo "   To change: azd env set AZURE_LOCATION <region>"
