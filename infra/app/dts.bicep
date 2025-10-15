param ipAllowlist array
param location string
param tags object = {}
param name string
param taskhubname string
param skuName string 
param skuCapacity int

resource dts 'Microsoft.DurableTask/schedulers@2025-11-01' = {
  location: location
  tags: tags
  name: name
  properties: {
    ipAllowlist: ipAllowlist
    sku: {
      name: skuName
      capacity: skuCapacity
    }
  }
}

resource taskhub 'Microsoft.DurableTask/schedulers/taskhubs@2025-11-01' = {
  parent: dts
  name: taskhubname
}

output dts_NAME string = dts.name
output dts_URL string = dts.properties.endpoint
output TASKHUB_NAME string = taskhub.name
