func getAdjustedRegion(location string, map object) string =>
  map.?overrides[?location] ?? (contains(map.?supportedRegions ?? [], location) ? location : (map.?default ?? location))

// See https://learn.microsoft.com/azure/ai-services/openai/concepts/models#model-summary-table-and-region-availability
var modelRegionMap = {
  'text-embedding-ada-002': {
    // Widely available in most Azure OpenAI regions
    supportedRegions: [
      'australiaeast', 'brazilsouth', 'canadaeast', 'eastus', 'eastus2', 'francecentral', 'japaneast'
      'northcentralus', 'norwayeast', 'southcentralus', 'swedencentral', 'switzerlandnorth', 'uksouth', 'westeurope', 'westus'
    ]
    overrides: {
      westus2: 'westus'
      westus3: 'westus'
    }
    default: 'eastus'
  }
  'text-embedding-3-small': {
    // Currently supported regions: 
    //    Australia East, Canada East, East US, East US 2, Japan East, Switzerland North, UAE North, West US
    supportedRegions: [
      'australiaeast', 'canadaeast', 'eastus', 'eastus2', 'japaneast', 'switzerlandnorth', 'uaenorth', 'westus'
    ]
    overrides: {
      westus2: 'westus'
      westus3: 'westus'
    }
    default: 'westus'
  }
  'gpt-4o': {
    // Currently supported regions: 
    //    Australia East, Brazil South, Canada East, East US, East US 2, France Central, Germany West Central, Italy North, 
    //    Japan East, Korea Central, North Central US, Norway East, Poland Central, South Africa North, South Central US,
    //    South India, Spain Central, Sweden Central, Switzerland North, UAE North, UK South, West Europe, West US, West US 3
    supportedRegions: [
      'australiaeast', 'brazilsouth', 'canadaeast', 'eastus', 'eastus2', 'francecentral', 'germanywestcentral', 'italynorth'
      'japaneast', 'koreacentral', 'northcentralus', 'norwayeast', 'polandcentral', 'southafricanorth', 'southcentralus'
      'southindia', 'spaincentral', 'swedencentral', 'switzerlandnorth', 'uaenorth', 'uksouth', 'westeurope', 'westus', 'westus3'
    ]
    overrides: {
      westus2: 'westus'
    }
    default: 'westus'
  }
  'gpt-4o-mini': {
    // Currently supported regions: 
    //    Australia East, Brazil South, Canada East, East US, East US 2, France Central, Germany West Central, Italy North, 
    //    Japan East, Korea Central, North Central US, Norway East, Poland Central, South Africa North, South Central US,
    //    South India, Spain Central, Sweden Central, Switzerland North, UAE North, UK South, West Europe, West US, West US 3
    supportedRegions: [
      'australiaeast', 'brazilsouth', 'canadaeast', 'eastus', 'eastus2', 'francecentral', 'germanywestcentral', 'italynorth'
      'japaneast', 'koreacentral', 'northcentralus', 'norwayeast', 'polandcentral', 'southafricanorth', 'southcentralus'
      'southindia', 'spaincentral', 'swedencentral', 'switzerlandnorth', 'uaenorth', 'uksouth', 'westeurope', 'westus', 'westus3'
    ]
    overrides: {
      westus2: 'westus'
    }
    default: 'westus'
  }
}

func getModelRegion(location string, modelName string) string => getAdjustedRegion(location, modelRegionMap[?modelName])

func getCognitiveServicesRegion(location string, chatModelName string, embeddingModelName string) string =>
  contains(modelRegionMap[?chatModelName].?supportedRegions, getModelRegion(location, embeddingModelName)) ? getModelRegion(getModelRegion(location, embeddingModelName), chatModelName): location

// See https://learn.microsoft.com/azure/ai-services/agents/concepts/model-region-support#azure-openai-models
// Currently supported regions:
//    Australia East, East US, East US 2, France Central, Japan East, Norway East, South India, Sweden Central,
//    UK South, West US, West US 3
var agentServiceRegionMap = {
  supportedRegions : [
    'australiaeast', 'eastus', 'eastus2', 'francecentral',  'japaneast', 'norwayeast', 'southindia', 'swedencentral'
    'uksouth', 'westus', 'westus3'
  ]
  overrides: {
    westus2: 'westus'
  }
  default: 'westus'
}

func getAgentServiceRegion(location string) string => getAdjustedRegion(location, agentServiceRegionMap)

@export()
@description('Based on an intended region, gets a supported region for the specified embedding model.')
func getAiServicesRegion(location string, chatModelName string, embeddingModelName string) string => getCognitiveServicesRegion(getAgentServiceRegion(location), chatModelName, embeddingModelName)

// See https://learn.microsoft.com/azure/azure-functions/flex-consumption-how-to#view-currently-supported-regions
// Currently supported regions: 
//    Australia East, Central India, East Asia, East US, East US 2, North Europe, Norway East, South Central US, 
//    Southeast Asia, Sweden Central, UK South, West Central US, West US 2, West US 3
var flexConsumptionRegionMap = {
  supportedRegions : [
    'australiaeast', 'centralindia', 'eastasia', 'eastus', 'eastus2', 'northeurope', 'norwayeast', 'southcentralus'
    'southeastasia', 'swedencentral', 'uksouth', 'westcentralus', 'westus2', 'westus3'
  ]
  overrides: {
    westus: 'westus2'
  }
  default: 'westus2'
}

@export()
@description('Based on an intended region, gets a supported region for Flex Consumption.')
func getFlexConsumptionRegion(location string) string => getAdjustedRegion(location, flexConsumptionRegionMap)
