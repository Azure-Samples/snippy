# Script to switch between DTS and Azure Storage backends for Durable Functions

param(
    [Parameter(Position=0)]
    [ValidateSet('dts', 'azureStorage', 'azureManaged', 'storage')]
    [string]$Backend = 'azureStorage'
)

$HostJsonPath = "src/host.json"

$McpConfig = @'
    "mcp": {
      "instructions": "Snippy is an intelligent code snippet service with AI-powered analysis. Available tools: save_snippet (save code with vector embeddings), get_snippet (retrieve saved snippets by name), deep_wiki (create comprehensive documentation), code_style (generate style guides from snippets), and generate_comprehensive_documentation (multi-agent orchestration that creates BOTH wiki docs AND style guide). Use save_snippet with 'snippetname' and 'snippet' parameters, optionally include 'projectid'. Retrieve snippets using get_snippet with 'snippetname'. For single-agent tasks, use deep_wiki or code_style with optional 'chathistory' and 'userquery'. For complete documentation packages, use generate_comprehensive_documentation with optional 'userquery' to focus the output.",
      "serverName": "Snippy",
      "serverVersion": "2.1.0",
      "messageOptions": {
        "useAbsoluteUriForEndpoint": false
      }
    },
'@

if ($Backend -eq 'dts' -or $Backend -eq 'azureManaged') {
    Write-Host "🔄 Switching to Durable Task Scheduler (DTS) backend..." -ForegroundColor Cyan
    
    $hostJson = @"
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
$McpConfig
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
"@
    
    $hostJson | Out-File -FilePath $HostJsonPath -Encoding utf8 -NoNewline
    
    Write-Host "✅ Switched to DTS backend" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Make sure your local.settings.json has:" -ForegroundColor Yellow
    Write-Host '   DTS_CONNECTION_STRING: "Endpoint=http://localhost:8080;Authentication=None"' -ForegroundColor Gray
    Write-Host '   TASKHUB_NAME: "default"' -ForegroundColor Gray
    Write-Host ""
    Write-Host "🐳 Start the DTS emulator:" -ForegroundColor Yellow
    Write-Host "   docker run -d -p 8080:8080 -p 8082:8082 mcr.microsoft.com/dts/dts-emulator:latest" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📊 DTS Dashboard: http://localhost:8082/" -ForegroundColor Magenta

} elseif ($Backend -eq 'azureStorage' -or $Backend -eq 'storage') {
    Write-Host "🔄 Switching to Azure Storage backend..." -ForegroundColor Cyan
    
    $hostJson = @"
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
$McpConfig
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
"@
    
    $hostJson | Out-File -FilePath $HostJsonPath -Encoding utf8 -NoNewline
    
    Write-Host "✅ Switched to Azure Storage backend" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Make sure your local.settings.json has:" -ForegroundColor Yellow
    Write-Host '   AzureWebJobsStorage: "UseDevelopmentStorage=true"' -ForegroundColor Gray
    Write-Host ""
    Write-Host "💾 Start Azurite:" -ForegroundColor Yellow
    Write-Host "   npm install -g azurite  # If not already installed" -ForegroundColor Gray
    Write-Host "   azurite                  # Run in a separate terminal" -ForegroundColor Gray
}
