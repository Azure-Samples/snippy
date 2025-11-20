#!/bin/bash
# Randomly select one of the allowed regions and set it as the default
# Run this script before 'azd provision' or 'azd up' to use a random region
# without being prompted. Otherwise, azd will prompt you to select a region.

# Check if AZURE_LOCATION is already set
EXISTING_LOCATION=$(azd env get-value AZURE_LOCATION 2>/dev/null)

if [ -n "$EXISTING_LOCATION" ]; then
    echo "ℹ️  AZURE_LOCATION is already set to: $EXISTING_LOCATION"
    echo "   Keeping existing location. To change, run: azd env set AZURE_LOCATION <region>"
else
    REGIONS=("westus2" "westus3" "eastus2", "northcentralus")
    RANDOM_INDEX=$((RANDOM % 3))
    SELECTED_REGION="${REGIONS[$RANDOM_INDEX]}"

    echo "🎲 Randomly selected region: $SELECTED_REGION"
    azd env set AZURE_LOCATION "$SELECTED_REGION"
    echo "✅ Region set. Run 'azd provision' to deploy without being prompted."
    echo "   To change: azd env set AZURE_LOCATION <region>"
fi
