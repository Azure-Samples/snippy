param principalID string
param roleDefinitionID string
param dtsName string
param principalType string

resource dts 'Microsoft.DurableTask/schedulers@2024-10-01-preview' existing = {
  name: dtsName
}

resource dtsRoleAssignment 'Microsoft.Authorization/roleAssignments@2020-04-01-preview' = {
  name: guid(dts.id, principalID, roleDefinitionID )
  scope: dts
  properties: {
   roleDefinitionId: resourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionID )
   principalId: principalID
   principalType: principalType
  }
}
