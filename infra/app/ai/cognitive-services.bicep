@description('Azure region of the deployment')
param location string

@description('Tags to add to the resources')
param tags object

@description('AI services name')
param aiServicesName string

@description('The embedding model name to deploy')
param embeddingModelName string = 'text-embedding-3-small'

@description('The embedding model format')
param embeddingModelFormat string = 'OpenAI'

@description('The embedding model SKU name')
param embeddingModelSkuName string = 'Standard'

@description('The embedding model capacity')
param embeddingModelCapacity int = 100

@description('The chat model name to deploy')
param chatModelName string = 'gpt-4o-mini'

@description('The chat model format')
param chatModelFormat string = 'OpenAI'

@description('The chat model SKU name')
param chatModelSkuName string = 'Standard'

@description('The chat model capacity')
param chatModelCapacity int = 100

resource aiServices 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiServicesName
  location: location
  tags: tags
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    customSubDomainName: toLower(aiServicesName)
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

resource embeddingModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: aiServices
  name: embeddingModelName
  sku: {
    capacity: embeddingModelCapacity
    name: embeddingModelSkuName
  }
  properties: {
    model: {
      format: embeddingModelFormat
      name: embeddingModelName
    }
  }
}

resource chatModelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-04-01-preview' = {
  parent: aiServices
  name: chatModelName
  sku: {
    name: chatModelSkuName
    capacity: chatModelCapacity
  }
  properties: {
    model: {
      format: chatModelFormat
      name: chatModelName
    }
  }
  dependsOn: [
    embeddingModelDeployment
  ]
}

output aiServicesName string = aiServices.name
output aiServicesId string = aiServices.id
output aiServicesEndpoint string = aiServices.properties.endpoint
output azureOpenAIServiceEndpoint string = 'https://${aiServices.properties.customSubDomainName}.openai.azure.com/'
output embeddingDeploymentName string = embeddingModelDeployment.name
output chatDeploymentName string = chatModelDeployment.name
