#!/bin/bash

# Script to switch between DTS and Azure Storage backends for Durable Functions

BACKEND=${1:-azureStorage}
HOST_JSON="src/host.json"

if [ "$BACKEND" = "dts" ] || [ "$BACKEND" = "azureManaged" ]; then
    echo "🔄 Switching to Durable Task Scheduler (DTS) backend..."
    
    # Update host.json to use DTS
    cat > "$HOST_JSON" << 'EOF'
{
  "version": "2.0",
  "logging": {
    "logLevel": {
      "Microsoft.Azure.WebJobs.Extensions.OpenAI": "Information"
    },
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle.Preview",
    "version": "[4.29.0, 5.0.0)"
  },
  "extensions": {
    "mcp": {
      "instructions": "Snippy is an intelligent code snippet service with AI-powered analysis. Available tools: save_snippet (save code with vector embeddings), get_snippet (retrieve saved snippets by name), deep_wiki (create comprehensive documentation), code_style (generate style guides from snippets), and generate_comprehensive_documentation (multi-agent orchestration that creates BOTH wiki docs AND style guide). Use save_snippet with 'snippetname' and 'snippet' parameters, optionally include 'projectid'. Retrieve snippets using get_snippet with 'snippetname'. For single-agent tasks, use deep_wiki or code_style with optional 'chathistory' and 'userquery'. For complete documentation packages, use generate_comprehensive_documentation with optional 'userquery' to focus the output.",
      "serverName": "Snippy",
      "serverVersion": "2.1.0",
      "messageOptions": {
        "useAbsoluteUriForEndpoint": false
      }
    },
    "durableTask": {
      "hubName": "%TASKHUB_NAME%",
      "storageProvider": {
        "type": "azureManaged",
        "connectionStringName": "DTS_CONNECTION_STRING"
      },
      "tracing": {
        "traceInputsAndOutputs": true
      }
    }
  }  
}
EOF
    
    echo "✅ Switched to DTS backend"
    echo ""
    echo "📝 Make sure your local.settings.json has:"
    echo "   DTS_CONNECTION_STRING: \"Endpoint=http://localhost:8080;Authentication=None\""
    echo "   TASKHUB_NAME: \"default\""
    echo ""
    echo "🐳 Start the DTS emulator:"
    echo "   docker run -d -p 8080:8080 -p 8082:8082 mcr.microsoft.com/dts/dts-emulator:latest"
    echo ""
    echo "📊 DTS Dashboard: http://localhost:8082/"

elif [ "$BACKEND" = "azureStorage" ] || [ "$BACKEND" = "storage" ]; then
    echo "🔄 Switching to Azure Storage backend..."
    
    # Update host.json to use Azure Storage
    cat > "$HOST_JSON" << 'EOF'
{
  "version": "2.0",
  "logging": {
    "logLevel": {
      "Microsoft.Azure.WebJobs.Extensions.OpenAI": "Information"
    },
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle.Preview",
    "version": "[4.29.0, 5.0.0)"
  },
  "extensions": {
    "mcp": {
      "instructions": "Snippy is an intelligent code snippet service with AI-powered analysis. Available tools: save_snippet (save code with vector embeddings), get_snippet (retrieve saved snippets by name), deep_wiki (create comprehensive documentation), code_style (generate style guides from snippets), and generate_comprehensive_documentation (multi-agent orchestration that creates BOTH wiki docs AND style guide). Use save_snippet with 'snippetname' and 'snippet' parameters, optionally include 'projectid'. Retrieve snippets using get_snippet with 'snippetname'. For single-agent tasks, use deep_wiki or code_style with optional 'chathistory' and 'userquery'. For complete documentation packages, use generate_comprehensive_documentation with optional 'userquery' to focus the output.",
      "serverName": "Snippy",
      "serverVersion": "2.1.0",
      "messageOptions": {
        "useAbsoluteUriForEndpoint": false
      }
    },
    "durableTask": {
      "hubName": "%TASKHUB_NAME%",
      "storageProvider": {
        "type": "azureStorage",
        "connectionStringName": "AzureWebJobsStorage"
      },
      "tracing": {
        "traceInputsAndOutputs": true
      }
    }
  }  
}
EOF
    
    echo "✅ Switched to Azure Storage backend"
    echo ""
    echo "📝 Make sure your local.settings.json has:"
    echo "   AzureWebJobsStorage: \"UseDevelopmentStorage=true\""
    echo ""
    echo "💾 Start Azurite:"
    echo "   npm install -g azurite  # If not already installed"
    echo "   azurite                  # Run in a separate terminal"

else
    echo "❌ Invalid backend: $BACKEND"
    echo ""
    echo "Usage: $0 [dts|azureStorage]"
    echo ""
    echo "Examples:"
    echo "  $0 dts           # Switch to Durable Task Scheduler"
    echo "  $0 azureStorage  # Switch to Azure Storage (for environments without Docker)"
    exit 1
fi
