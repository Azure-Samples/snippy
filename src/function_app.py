# =============================================================================
# AZURE FUNCTIONS APPLICATION WITH INTEGRATED AI SERVICES
# =============================================================================
#
# This application demonstrates a modern AI-powered code snippet manager built with:
#
# 1. Azure Functions - Serverless compute that runs your code in the cloud
#    - HTTP triggers - Standard RESTful API endpoints accessible over HTTP
#    - MCP triggers - Model Context Protocol for AI agent integration (e.g., GitHub Copilot)
#
# 2. Azure Cosmos DB - NoSQL database with vector search capability
#    - Stores code snippets and their vector embeddings
#    - Enables semantic search through vector similarity
#
# 3. Azure OpenAI - Provides AI models and embeddings
#    - Generates vector embeddings from code snippets
#    - These embeddings capture the semantic meaning of the code
#
# 4. Azure AI Agents - Specialized AI agents for code analysis
#    - For generating documentation and style guides from snippets
#
# The application provides two parallel interfaces for the same functionality:
# - HTTP endpoints for traditional API access
# - MCP tools for AI assistant integration

import json
import logging
import azure.functions as func
from data import cosmos_ops  # Module for Cosmos DB operations
from agents import deep_wiki, code_style  # Modules for AI agent operations
from tool_helpers import ToolProperty, ToolPropertyList  # Helper classes for tool definitions

# Initialize the Azure Functions app
# This is the main entry point for all function definitions
app = func.FunctionApp()

# =============================================================================
# CONSTANTS
# =============================================================================

# Constants for input property names in MCP tool definitions
# These define the expected property names for inputs to MCP tools
_SNIPPET_NAME_PROPERTY_NAME = "snippetname"  # Property name for the snippet identifier
_SNIPPET_PROPERTY_NAME = "snippet"           # Property name for the snippet content
_PROJECT_ID_PROPERTY_NAME = "projectid"      # Property name for the project identifier
_CHAT_HISTORY_PROPERTY_NAME = "chathistory"  # Property name for previous chat context
_USER_QUERY_PROPERTY_NAME = "userquery"      # Property name for the user's specific question

# =============================================================================
# TOOL PROPERTY DEFINITIONS
# =============================================================================
# Each MCP tool needs a schema definition to describe its expected inputs.
# This is how AI assistants know what parameters to provide when using these tools.
# Tool properties are passed to the @app.mcp_tool_trigger decorator via
# the `tool_properties` parameter (as a JSON-serialized string).

# Properties for the save_snippet tool
# This tool saves code snippets with their vector embeddings
tool_properties_save_snippets = ToolPropertyList(
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "A unique name or identifier for the code snippet. Provide this if you have a specific name for the snippet being saved. Essential for identifying the snippet later."),
    ToolProperty(_PROJECT_ID_PROPERTY_NAME, "string", "An identifier for a project to associate this snippet with. Useful for organizing snippets. If omitted or not relevant, it defaults to 'default-project'."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The actual code or text content of the snippet. Provide the content that needs to be saved and made searchable."),
)

# Properties for the get_snippet tool
# This tool retrieves previously saved snippets by name
tool_properties_get_snippets = ToolPropertyList(
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The unique name or identifier of the code snippet you want to retrieve. This is required to fetch a specific snippet."),
)

# Properties for the deep_wiki tool
# This tool generates comprehensive documentation from code snippets
tool_properties_wiki = ToolPropertyList(
    ToolProperty(_CHAT_HISTORY_PROPERTY_NAME, "string", "Optional. The preceding conversation history (e.g., user prompts and AI responses). Providing this helps contextualize the wiki content generation. Omit if no relevant history exists or if a general wiki is desired."),
    ToolProperty(_USER_QUERY_PROPERTY_NAME, "string", "Optional. The user's specific question, instruction, or topic to focus the wiki documentation on. If omitted, a general wiki covering available snippets might be generated."),
)

# Properties for the code_style tool
# This tool generates coding style guides based on existing snippets
tool_properties_code_style = ToolPropertyList(
    ToolProperty(_CHAT_HISTORY_PROPERTY_NAME, "string", "Optional. The preceding conversation history (e.g., user prompts and AI responses). This can provide context for the code style analysis or guide generation. Omit if not available or not relevant."),
    ToolProperty(_USER_QUERY_PROPERTY_NAME, "string", "Optional. The user's specific question, instruction, or prompt related to code style. If omitted, a general code style analysis or a default guide might be generated."),
)

# =============================================================================
# SAVE SNIPPET FUNCTIONALITY
# =============================================================================

# HTTP endpoint for saving snippets
# This is accessible via standard HTTP POST requests
@app.route(route="snippets", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
@app.embeddings_input(arg_name="embeddings", input="{code}", input_type="rawText", embeddings_model="%EMBEDDING_MODEL_DEPLOYMENT_NAME%")
async def http_save_snippet(req: func.HttpRequest, embeddings: str) -> func.HttpResponse:
    """
    HTTP trigger function to save a code snippet with its vector embedding.
    
    Key features:
    - Takes a JSON payload with 'name', 'code', and optional 'projectId'
    - Uses Azure OpenAI to automatically generate vector embeddings
    - Stores the snippet and its embedding in Cosmos DB
    
    The @app.embeddings_input decorator:
    - Automatically calls Azure OpenAI to generate embeddings before the function runs
    - Extracts 'code' from the request body
    - Generates a vector embedding for that code
    - Passes the embedding to the function via the 'embeddings' parameter
    """
    try:
        # 1. Extract and validate the request body
        req_body = req.get_json()
        required_fields = ["name", "code"]
        for field in required_fields:
            if field not in req_body:
                # Return a 400 Bad Request if required fields are missing
                return func.HttpResponse(
                    body=json.dumps({"error": f"Missing required field: {field}"}),
                    mimetype="application/json",
                    status_code=400)
        
        # 2. Extract the snippet details from the request
        project_id = req_body.get("projectId", "default-project")  # Use default if not provided
        name = req_body["name"]
        code = req_body["code"]

        # 3. Log some details about the snippet being saved
        logging.info(f"Input text length: {len(code)} characters")
        logging.info(f"Input text preview: {code[:100]}...")
        
        try:
            # 4. Process the embeddings generated by Azure OpenAI
            # The embeddings are provided as a JSON string that needs to be parsed
            embeddings_data = json.loads(embeddings)
            
            # 5. Extract the actual vector from the embeddings response
            # This is the numerical representation of the code's meaning
            embedding_vector = embeddings_data["response"]["data"][0]["embedding"]
            
            # 6. Save the snippet and its embedding to Cosmos DB
            result = await cosmos_ops.upsert_document(
                name=name,
                project_id=project_id,
                code=code,
                embedding=embedding_vector
            )
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # Handle errors in embedding processing
            logging.error(f"Embeddings processing error: {str(e)}")
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid embeddings data or structure"}),
                mimetype="application/json",
                status_code=500)
        
        # 7. Return success response with the result from Cosmos DB
        return func.HttpResponse(body=json.dumps(result), mimetype="application/json", status_code=200)
    except Exception as e:
        # General error handling
        logging.error(f"Error in http_save_snippet: {str(e)}")
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)

# MCP tool for saving snippets
# This is accessible to AI assistants via the MCP protocol
@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="save_snippet",
    description="Saves a given code snippet. It can take a snippet name, the snippet content, and an optional project ID. Embeddings are generated for the content to enable semantic search. The LLM should provide 'snippetname' and 'snippet' when intending to save.",
    tool_properties=tool_properties_save_snippets.to_json(),
)
@app.embeddings_input(arg_name="embeddings", input="{arguments.snippet}", input_type="rawText", embeddings_model="%EMBEDDING_MODEL_DEPLOYMENT_NAME%")
async def mcp_save_snippet(context: str, embeddings: str) -> str:
    """
    MCP tool to save a code snippet with vector embedding.
    
    Key features:
    - Receives parameters from an AI assistant like GitHub Copilot
    - Uses the same embedding generation as the HTTP endpoint
    - Shares the same storage logic with the HTTP endpoint
    
    The difference from the HTTP endpoint:
    - Receives parameters via the 'context' JSON string (containing 'arguments') instead of HTTP body
    - Returns results as a JSON string instead of an HTTP response object
    - Uses {arguments.snippet} in the @app.embeddings_input decorator to reference
      the snippet content from the context's 'arguments' object
    """
    try:
        # 1. Parse the context JSON string to extract the arguments
        mcp_data = json.loads(context)
        args = mcp_data.get("arguments", {})

        # 2. Extract snippet details from the arguments
        name = args.get(_SNIPPET_NAME_PROPERTY_NAME)  # Snippet name
        code = args.get(_SNIPPET_PROPERTY_NAME)       # Snippet content
        project_id = args.get(_PROJECT_ID_PROPERTY_NAME, "default-project")  # Use default if not provided

        # 3. Validate required parameters
        if not name or not code:
            missing_fields = []
            if not name: missing_fields.append(_SNIPPET_NAME_PROPERTY_NAME)
            if not code: missing_fields.append(_SNIPPET_PROPERTY_NAME)
            return json.dumps({"error": f"Missing essential arguments for save_snippet: {', '.join(missing_fields)}. Please provide both snippet name and content."})

        # 4. Log some details about the snippet being saved
        logging.info(f"Input text length: {len(code)} characters")
        logging.info(f"Input text preview: {code[:100]}...")
        
        try:
            # 5. Process the embeddings generated by Azure OpenAI
            embeddings_data = json.loads(embeddings)
            
            # 6. Extract the vector from the embeddings response
            embedding_vector = embeddings_data["response"]["data"][0]["embedding"]
            
            # 7. Save the snippet and its embedding to Cosmos DB
            # Uses the same storage function as the HTTP endpoint
            result = await cosmos_ops.upsert_document(name=name, project_id=project_id, code=code, embedding=embedding_vector)
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            # Handle errors in embedding processing
            logging.error(f"Embeddings processing error: {str(e)}")
            return json.dumps({"error": "Invalid embeddings data or structure"})
        
        # 8. Return success result as a JSON string
        return json.dumps(result)
    except json.JSONDecodeError:
        # Handle invalid context JSON
        return json.dumps({"error": "Invalid JSON received in context"})
    except Exception as e: 
        # General error handling
        logging.error(f"Error in mcp_save_snippet: {str(e)}")
        return json.dumps({"error": str(e)})

# =============================================================================
# GET SNIPPET FUNCTIONALITY
# =============================================================================

# HTTP endpoint for retrieving snippets
# This is accessible via standard HTTP GET requests
@app.route(route="snippets/{name}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def http_get_snippet(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger function to retrieve a code snippet by name.
    
    Key features:
    - Takes the snippet name from the URL path parameter
    - Retrieves the snippet from Cosmos DB
    - Returns the snippet as a JSON response
    
    No embedding generation is needed for retrieval by name.
    """
    try:
        # 1. Extract the snippet name from the route parameters
        name = req.route_params.get("name")
        if not name:
            # Return a 400 Bad Request if the name is missing
            return func.HttpResponse(body=json.dumps({"error": "Missing snippet name in route"}), mimetype="application/json", status_code=400)
        
        # 2. Retrieve the snippet from Cosmos DB
        snippet = await cosmos_ops.get_snippet_by_id(name)
        if not snippet:
            # Return a 404 Not Found if the snippet doesn't exist
            return func.HttpResponse(body=json.dumps({"error": f"Snippet '{name}' not found"}), mimetype="application/json", status_code=404)
        
        # 3. Return the snippet as a JSON response
        return func.HttpResponse(body=json.dumps(snippet), mimetype="application/json", status_code=200)
    except Exception as e:
        # General error handling
        logging.error(f"Error in http_get_snippet: {str(e)}")
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)

# MCP tool for retrieving snippets
# This is accessible to AI assistants via the MCP protocol
@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="get_snippet",
    description="Retrieves a previously saved code snippet using its unique name. The LLM should provide the 'snippetname' when it intends to fetch a specific snippet.",
    tool_properties=tool_properties_get_snippets.to_json(),
)
async def mcp_get_snippet(context) -> str:
    """
    MCP tool to retrieve a code snippet by name.
    
    Key features:
    - Receives the snippet name from an AI assistant
    - Uses the same retrieval logic as the HTTP endpoint
    - Returns the snippet as a JSON string
    
    The difference from the HTTP endpoint:
    - Receives the snippet name via the 'context' JSON string (containing 'arguments')
      instead of from the URL path parameter
    - Returns results as a JSON string instead of an HTTP response object
    """
    try:
        # 1. Parse the context JSON string to extract the arguments
        mcp_data = json.loads(context)
        args = mcp_data.get("arguments", {})
        
        # 2. Extract the snippet name from the arguments
        name = args.get(_SNIPPET_NAME_PROPERTY_NAME)

        # 3. Validate the required parameter
        if not name:
            return json.dumps({"error": f"Missing essential argument for get_snippet: {_SNIPPET_NAME_PROPERTY_NAME}. Please provide the snippet name to retrieve."})
        
        # 4. Retrieve the snippet from Cosmos DB
        # Uses the same storage function as the HTTP endpoint
        snippet = await cosmos_ops.get_snippet_by_id(name)
        if not snippet:
            # Return an error if the snippet doesn't exist
            return json.dumps({"error": f"Snippet '{name}' not found"})
        
        # 5. Return the snippet as a JSON string
        return json.dumps(snippet)
    except json.JSONDecodeError:
        # Handle invalid context JSON
        return json.dumps({"error": "Invalid JSON received in context"})
    except Exception as e:
        # General error handling
        logging.error(f"Error in mcp_get_snippet: {str(e)}")
        return json.dumps({"error": str(e)})

# =============================================================================
# CODE STYLE GUIDE FUNCTIONALITY
# =============================================================================

# HTTP endpoint for generating code style guides
# This is accessible via standard HTTP POST requests
@app.route(route="snippets/code-style", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def http_code_style(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to generate a code style guide based on saved snippets.
    
    Key features:
    - Takes optional chat history and user query from the request body
    - Uses AI to analyze saved code snippets
    - Generates a style guide as markdown content
    
    This leverages Azure AI to analyze patterns in the code snippets
    and generate a coherent style guide that can be saved by the client.
    """
    try:
        logging.info("HTTP: Starting code style content generation")
        
        # 1. Extract the request body, defaulting to an empty object if not provided
        req_body = req.get_json() if req.get_body() else {} 
        
        # 2. Extract optional parameters from the request
        chat_history = req_body.get("chatHistory", "")  # Previous conversation for context
        user_query = req_body.get("userQuery", "")      # Specific user question or focus
        
        # 3. Generate the code style guide using the AI agent
        # This will analyze saved snippets and generate appropriate content
        style_guide_content = await code_style.generate_code_style(
            chat_history=chat_history,
            user_query=user_query
        )
        logging.info("HTTP: Successfully generated code style content")
        
        # 4. Return the generated content as a JSON response
        return func.HttpResponse(
            body=json.dumps({"styleGuideContent": style_guide_content}), 
            mimetype="application/json", 
            status_code=200
        )
    except Exception as e:
        # General error handling with full stack trace
        logging.error(f"Error in http_code_style: {str(e)}", exc_info=True)
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)

# MCP tool for generating code style guides
# This is accessible to AI assistants via the MCP protocol
@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="code_style",
    description="Generates a code style guide. This involves creating content for a new file (e.g., 'code-style-guide.md' to be placed in the workspace root). Optional 'chathistory' and 'userquery' can be supplied to customize or focus the guide; omit them for a general or default style guide.",
    tool_properties=tool_properties_code_style.to_json(),
)
async def mcp_code_style(context) -> str:
    """
    MCP tool to generate a code style guide based on saved snippets.
    
    Key features:
    - Receives optional parameters from an AI assistant
    - Uses the same AI agent as the HTTP endpoint
    - Returns the generated content as a JSON string
    
    The difference from the HTTP endpoint:
    - Receives parameters via the 'context' JSON string (containing 'arguments')
      instead of HTTP body
    - Returns results as a JSON string instead of an HTTP response object
    """
    try:
        logging.info("MCP: Starting code style content generation")
        
        # 1. Parse the context JSON string to extract the arguments
        mcp_data = json.loads(context)
        args = mcp_data.get("arguments", {})
        
        # 2. Extract optional parameters from the arguments
        chat_history = args.get(_CHAT_HISTORY_PROPERTY_NAME, "")  # Previous conversation for context
        user_query = args.get(_USER_QUERY_PROPERTY_NAME, "")      # Specific user question or focus
        
        # 3. Generate the code style guide using the AI agent
        # Uses the same function as the HTTP endpoint
        style_guide_content = await code_style.generate_code_style(
            chat_history=chat_history,
            user_query=user_query
        )
        logging.info("MCP: Successfully generated code style content")
        
        # 4. Return the generated content as a JSON string
        return json.dumps({"styleGuideContent": style_guide_content})
    except json.JSONDecodeError:
        # Handle invalid context JSON
        return json.dumps({"error": "Invalid JSON received in context"})
    except Exception as e:
        # General error handling with full stack trace
        logging.error(f"Error in mcp_code_style: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})

# =============================================================================
# DEEP WIKI FUNCTIONALITY
# =============================================================================

# HTTP endpoint for generating comprehensive wiki documentation
# This is accessible via standard HTTP POST requests
@app.route(route="snippets/wiki", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def http_deep_wiki(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP trigger to generate comprehensive wiki documentation based on saved snippets.
    
    Key features:
    - Takes optional chat history and user query from the request body
    - Uses AI to analyze saved code snippets
    - Generates detailed documentation as markdown content
    
    This creates interconnected documentation that explains the code snippets
    and their relationships, suitable for creating a developer wiki.
    """
    try:
        logging.info("HTTP: Starting deep wiki content generation")
        
        # 1. Extract the request body, defaulting to an empty object if not provided
        req_body = req.get_json() if req.get_body() else {} 
        
        # 2. Extract optional parameters from the request
        chat_history = req_body.get("chatHistory", "")  # Previous conversation for context
        user_query = req_body.get("userQuery", "")      # Specific user question or focus
        
        # 3. Generate the wiki documentation using the AI agent
        # This will analyze saved snippets and generate appropriate content
        wiki_content = await deep_wiki.generate_deep_wiki(
            chat_history=chat_history,
            user_query=user_query
        )
        logging.info("HTTP: Successfully generated deep wiki content")
        
        # 4. Return the generated content as markdown
        # Note the mimetype is text/markdown, not application/json
        return func.HttpResponse(body=wiki_content, mimetype="text/markdown", status_code=200)
    except Exception as e:
        # General error handling
        logging.error(f"Error in http_deep_wiki: {str(e)}")
        return func.HttpResponse(body=json.dumps({"error": str(e)}), mimetype="application/json", status_code=500)

# MCP tool for generating comprehensive wiki documentation
# This is accessible to AI assistants via the MCP protocol
@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="deep_wiki",
    description="Creates comprehensive 'deep wiki' documentation. This involves generating content for a new wiki file (e.g., 'deep-wiki.md' to be placed in the workspace root), often by analyzing existing code snippets. Optional 'chathistory' and 'userquery' can be provided to refine or focus the wiki content; omit them for a general wiki.",
    tool_properties=tool_properties_wiki.to_json(),
)
async def mcp_deep_wiki(context) -> str:
    """
    MCP tool to generate comprehensive wiki documentation based on saved snippets.
    
    Key features:
    - Receives optional parameters from an AI assistant
    - Uses the same AI agent as the HTTP endpoint
    - Returns the generated content as a markdown string
    
    The difference from the HTTP endpoint:
    - Receives parameters via the 'context' JSON string (containing 'arguments')
      instead of HTTP body
    - Returns the raw markdown string directly instead of an HTTP response object
      (This is an exception to the usual pattern of returning JSON-wrapped results)
    """
    try:
        logging.info("MCP: Starting deep wiki content generation")
        
        # 1. Parse the context JSON string to extract the arguments
        mcp_data = json.loads(context)
        args = mcp_data.get("arguments", {})

        # 2. Extract optional parameters from the arguments
        chat_history = args.get(_CHAT_HISTORY_PROPERTY_NAME, "")  # Previous conversation for context
        user_query = args.get(_USER_QUERY_PROPERTY_NAME, "")      # Specific user question or focus
        
        # 3. Generate the wiki documentation using the AI agent
        # Uses the same function as the HTTP endpoint
        wiki_content = await deep_wiki.generate_deep_wiki(
            chat_history=chat_history,
            user_query=user_query
        )
        logging.info("MCP: Successfully generated deep wiki content")
        
        # 4. Return the raw markdown content
        # Note: Unlike other MCP tools, this returns raw markdown, not JSON
        return wiki_content 
    except json.JSONDecodeError:
        # Handle invalid context JSON
        return json.dumps({"error": "Invalid JSON received in context"})
    except Exception as e:
        # General error handling
        logging.error(f"Error in mcp_deep_wiki: {str(e)}")
        return json.dumps({"error": str(e)})