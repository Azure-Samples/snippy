param name string
param location string = resourceGroup().location
param tags object = {}
param applicationInsightsName string = ''
param appSettings object = {}
param serviceName string = 'api'
param storageAccountName string
param deploymentStorageContainerName string
param virtualNetworkSubnetId string = ''
param instanceMemoryMB int = 2048
param maximumInstanceCount int = 100
param identityId string = ''
param identityClientId string = ''
param resourceToken string
param actualSuffix string

param runtimeName string = 'python'
param runtimeVersion string = '3.11'

@allowed(['SystemAssigned', 'UserAssigned'])
param identityType string = 'UserAssigned'

import * as regionSelector from './util/region-selector.bicep'
var abbrs = loadJsonContent('../abbreviations.json')

var applicationInsightsIdentity = 'ClientId=${identityClientId};Authorization=AAD'

// The application backend is a function app
module appServicePlan 'br/public:avm/res/web/serverfarm:0.1.1' = {
  name: 'appserviceplan'
  params: {
    name: '${abbrs.webServerFarms}${resourceToken}-${actualSuffix}'
    location: regionSelector.getFlexConsumptionRegion(location)
    tags: tags
    sku: {
      name: 'FC1'
      tier: 'FlexConsumption'
    }
    reserved: true
  }
}

resource stg 'Microsoft.Storage/storageAccounts@2022-09-01' existing = {
  name: storageAccountName
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' existing = if (!empty(applicationInsightsName)) {
  name: applicationInsightsName
}

module api 'br/public:avm/res/web/site:0.15.1' = {
  name: '${serviceName}-functions-module'
  params: {
    name: name
    location: location
    kind: 'functionapp,linux'
    tags: union(tags, { 'azd-service-name': serviceName })
    managedIdentities: {
      systemAssigned: identityType == 'SystemAssigned'
      userAssignedResourceIds: [
        '${identityId}'
      ]
    }
    serverFarmResourceId: appServicePlan.outputs.resourceId
    functionAppConfig: {
      location: location
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${stg.properties.primaryEndpoints.blob}${deploymentStorageContainerName}'
          authentication: {
            type: identityType == 'SystemAssigned' ? 'SystemAssignedIdentity' : 'UserAssignedIdentity'
            userAssignedIdentityResourceId: identityType == 'UserAssigned' ? identityId : '' 
          }
        }
      }
      scaleAndConcurrency: {
        instanceMemoryMB: instanceMemoryMB
        maximumInstanceCount: maximumInstanceCount
        alwaysReady: [
          {
            name: 'http'
            instanceCount: 1
          }
          {
            name: 'durable'
            instanceCount: 1
          }
        ]
      }
      runtime: {
        name: runtimeName
        version: runtimeVersion
      }
    }
    appSettingsKeyValuePairs: union(appSettings,
      {
        AzureWebJobsStorage__blobServiceUri: stg.properties.primaryEndpoints.blob
        AzureWebJobsStorage__queueServiceUri: stg.properties.primaryEndpoints.queue
        AzureWebJobsStorage__tableServiceUri: stg.properties.primaryEndpoints.table
        AzureWebJobsStorage__credential: 'managedidentity'
        AzureWebJobsStorage__clientId : identityClientId
        APPLICATIONINSIGHTS_CONNECTION_STRING: applicationInsights.properties.ConnectionString
        APPLICATIONINSIGHTS_AUTHENTICATION_STRING: applicationInsightsIdentity
        AzureWebJobsFeatureFlags: 'EnableWorkerIndexing'
        PYTHON_ENABLE_WORKER_EXTENSIONS: '1'
      })
    virtualNetworkSubnetId: !empty(virtualNetworkSubnetId) ? virtualNetworkSubnetId : null
    siteConfig: {
      alwaysOn: false
    }
  }
}

output SERVICE_API_NAME string = api.outputs.name
output SERVICE_API_IDENTITY_PRINCIPAL_ID string = identityType == 'SystemAssigned' ? api.outputs.?systemAssignedMIPrincipalId ?? '' : ''
