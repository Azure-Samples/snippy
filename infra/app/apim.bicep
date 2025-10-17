@description('The name of the API Management service')
param name string

@description('The location for the API Management service')
param location string = resourceGroup().location

@description('Tags to apply to the API Management service')
param tags object = {}

@description('The name of the organization for the API Management service')
param publisherName string

@description('The email address of the organization for the API Management service')
param publisherEmail string

@description('The SKU of the API Management service')
@allowed(['BasicV2'])
param skuName string = 'BasicV2'

@description('The instance size of the API Management service')
param skuCapacity int = 1

@description('Enable or disable public network access')
@allowed(['Enabled', 'Disabled'])
param publicNetworkAccess string = 'Enabled'

@description('App Registration Client ID for MCP')
param appRegistrationClientId string = ''

@description('Azure Entra Tenant ID')
param tenantId string = tenant().tenantId

resource apiManagement 'Microsoft.ApiManagement/service@2023-05-01-preview' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  properties: {
    publisherName: publisherName
    publisherEmail: publisherEmail
    publicNetworkAccess: publicNetworkAccess
    customProperties: {
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls10': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Tls11': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Protocols.Ssl30': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls10': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Tls11': 'false'
      'Microsoft.WindowsAzure.ApiManagement.Gateway.Security.Backend.Protocols.Ssl30': 'false'
    }
  }
  identity: {
    type: 'SystemAssigned'
  }
}

// Named Value: APIMGateway - APIM Gateway URL
resource namedValueAPIMGateway 'Microsoft.ApiManagement/service/namedValues@2023-05-01-preview' = {
  parent: apiManagement
  name: 'APIMGateway'
  properties: {
    displayName: 'APIMGateway'
    value: apiManagement.properties.gatewayUrl
  }
}

// Named Value: McpClientID - App Registration Client ID
resource namedValueMcpClientID 'Microsoft.ApiManagement/service/namedValues@2023-05-01-preview' = if (!empty(appRegistrationClientId)) {
  parent: apiManagement
  name: 'McpClientID'
  properties: {
    displayName: 'McpClientID'
    value: appRegistrationClientId
  }
}

// Named Value: McpTenantID - Azure Entra Tenant ID
resource namedValueMcpTenantID 'Microsoft.ApiManagement/service/namedValues@2023-05-01-preview' = {
  parent: apiManagement
  name: 'McpTenantID'
  properties: {
    displayName: 'McpTenantID'
    value: tenantId
  }
}

// Outputs
output apiManagementId string = apiManagement.id
output apiManagementName string = apiManagement.name
output gatewayUrl string = apiManagement.properties.gatewayUrl
output managementApiUrl string = apiManagement.properties.managementApiUrl
output principalId string = apiManagement.identity.principalId
