import json

class ToolProperty:
    """
    Defines a property for an MCP tool, including its name, data type, and description.
    
    These properties are used by AI assistants (like GitHub Copilot) to understand:
    - What inputs each tool expects
    - What data types those inputs should be
    - How to describe each input to users
    
    This helps the AI to correctly invoke the tool with appropriate parameters.
    """
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name    # Name of the property
        self.propertyType = property_type    # Data type (string, number, etc.)
        self.description = description       # Human-readable description
        
    def to_dict(self) -> dict:
        """
        Converts the property definition to a dictionary format for JSON serialization.
        Required for MCP tool registration.
        """
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


class ToolPropertyList:
    """
    Manages a collection of ToolProperty objects and provides JSON serialization.
    
    Simplifies creating and serializing lists of tool properties for MCP tool registration.
    """
    def __init__(self, *properties: ToolProperty):
        """
        Initialize with zero or more ToolProperty instances.
        
        Args:
            *properties: Variable number of ToolProperty objects.
        """
        self.properties = list(properties)
    
    def to_json(self):
        """
        Returns a JSON string representation of the property list.
        
        Returns:
            JSON string containing the serialized properties.
        """
        return json.dumps([prop.to_dict() for prop in self.properties])
 