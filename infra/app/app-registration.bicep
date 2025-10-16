@description('The display name for the app registration')
param displayName string

// These values should be provided after running scripts/create-app-registration.sh
@description('The application (client) ID from the pre-created app registration')
param applicationId string

@description('The object ID from the pre-created app registration')
param objectId string = ''

@description('The scope ID from the pre-created app registration')
param scopeId string

// Computed outputs based on provided values
var applicationIdUri = 'api://${applicationId}'

// Outputs - passing through the provided values
output applicationId string = applicationId
output objectId string = objectId
output applicationIdUri string = applicationIdUri
output servicePrincipalId string = objectId  // Can be updated if needed
output scopeId string = scopeId
output displayName string = displayName
