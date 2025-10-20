param principalId string
param roleDefinitionId string
param aiProjectName string
param principalType string = 'ServicePrincipal'

resource aiProject 'Microsoft.MachineLearningServices/workspaces@2025-01-01-preview' existing = {
  name: aiProjectName
}

resource aiProjectRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiProject.id, principalId, roleDefinitionId)
  scope: aiProject
  properties: {
    principalId: principalId
    roleDefinitionId:  resourceId('Microsoft.Authorization/roleDefinitions', roleDefinitionId)
    principalType: principalType
  }
}

output ROLE_ASSIGNMENT_NAME string = aiProjectRoleAssignment.name
