@description('The name of the Azure OpenAI account')
param openAIAccountName string

@description('The role definition ID for the role assignment')
param roleDefinitionId string

@description('The principal ID to assign the role to')
param principalId string

@description('The type of principal (User, Group, or ServicePrincipal)')
@allowed(['User', 'Group', 'ServicePrincipal'])
param principalType string = 'ServicePrincipal'

resource openAIAccount 'Microsoft.CognitiveServices/accounts@2023-05-01' existing = {
  name: openAIAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(openAIAccount.id, principalId, roleDefinitionId)
  scope: openAIAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalId: principalId
    principalType: principalType
  }
}
