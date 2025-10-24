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
# 4. agent-framework-azurefunctions - Durable AI Agents using Durable Entities
#    - For generating documentation and style guides from snippets
#    - Automatic state persistence and conversation history
#    - Built-in resilience and error handling
#
# The application showcases:
# - Traditional HTTP endpoints for snippet management
# - MCP tools for AI assistant integration
# - Durable Agent endpoints powered by agent-framework-azurefunctions

import json
import logging
import azure.functions as func
from data import cosmos_ops  # Module for Cosmos DB operations
from tool_helpers import ToolProperty, ToolPropertyList  # Helper classes for tool definitions

# Import the AgentFunctionApp which includes both agents and allows orchestrations
from agents.durable_agents import app

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

# Properties for the generate_comprehensive_documentation tool
# This tool coordinates multiple agents to generate complete documentation
tool_properties_comprehensive_docs = ToolPropertyList(
    ToolProperty(_USER_QUERY_PROPERTY_NAME, "string", "Optional. A specific query or focus area for the documentation. This can guide the multi-agent orchestration to emphasize particular aspects (e.g., 'Focus on API patterns' or 'Emphasize security best practices'). If omitted, generates comprehensive documentation covering all aspects."),
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
# NOTE: The following HTTP endpoint for code_style has been replaced
# by agent-framework-azurefunctions endpoints.
# Use POST /api/agents/CodeStyleAgent/run instead.
#
# # HTTP endpoint for generating code style guides
# # This is accessible via standard HTTP POST requests
# @app.route(route="snippets/code-style", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
# async def http_code_style(req: func.HttpRequest) -> func.HttpResponse:
#     ... (commented out - use agent-framework endpoint instead)

# NOTE: The following HTTP and MCP triggers for code_style have been replaced
# by agent-framework-azurefunctions endpoints above.
# Use POST /api/agents/CodeStyleAgent/run instead.
#
# # HTTP endpoint for generating code style guides
# # This is accessible via standard HTTP POST requests
# @app.route(route="snippets/code-style", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
# async def http_code_style(req: func.HttpRequest) -> func.HttpResponse:
#     ... (commented out - use agent-framework endpoint instead)

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
    MCP tool to generate a code style guide using the CodeStyleAgent.
    
    This trigger directly invokes the CodeStyleAgent to generate a style guide.
    The agent uses vector search to find code snippets and analyzes coding patterns.
    """
    try:
        logging.info("MCP: code_style trigger - invoking CodeStyleAgent directly")
        
        # Import the agent
        from agents.durable_agents import code_style_agent
        
        # Parse the context
        mcp_data = json.loads(context)
        args = mcp_data.get("arguments", {})
        
        # Build message for the agent
        chat_history = args.get(_CHAT_HISTORY_PROPERTY_NAME, "")
        user_query = args.get(_USER_QUERY_PROPERTY_NAME, "")
        
        if chat_history and user_query:
            message = f"Context: {chat_history}\n\nQuery: {user_query}"
        elif user_query:
            message = user_query
        else:
            message = "Generate a comprehensive code style guide based on the code snippets."
        
        # Call the agent directly
        result = await code_style_agent.run(messages=message)
        
        # Extract the response text from the last message
        # result.messages is a list of ChatMessage objects
        # Each message has a 'contents' list containing TextContent objects
        # We need to extract the text from the TextContent objects
        response_text = ""
        if result.messages:
            last_message = result.messages[-1]
            if hasattr(last_message, 'contents') and last_message.contents:
                # Get text from all content items
                response_text = "".join(
                    content.text if hasattr(content, 'text') else str(content)
                    for content in last_message.contents
                )
        
        logging.info(f"MCP: code_style completed successfully")
        return json.dumps({
            "success": True,
            "style_guide": response_text,
            "message": "Code style guide generated successfully"
        })
        
    except Exception as e:
        logging.error(f"Error in mcp_code_style: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})

# =============================================================================
# DEEP WIKI FUNCTIONALITY
# =============================================================================

# NOTE: The following HTTP endpoint for deep_wiki has been replaced
# by agent-framework-azurefunctions endpoints above.
# Use POST /api/agents/DeepWikiAgent/run instead.
#
# # HTTP endpoint for generating comprehensive wiki documentation
# # This is accessible via standard HTTP POST requests
# @app.route(route="snippets/wiki", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
# async def http_deep_wiki(req: func.HttpRequest) -> func.HttpResponse:
#     ... (commented out - use agent-framework endpoint instead)

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
    MCP tool to generate comprehensive wiki documentation using the DeepWikiAgent.
    
    This trigger directly invokes the DeepWikiAgent to generate wiki documentation.
    The agent uses vector search to find code snippets and generates comprehensive documentation.
    """
    try:
        logging.info("MCP: deep_wiki trigger - invoking DeepWikiAgent directly")
        
        # Import the agent
        from agents.durable_agents import deep_wiki_agent
        
        # Parse the context
        mcp_data = json.loads(context)
        args = mcp_data.get("arguments", {})
        
        # Build message for the agent
        chat_history = args.get(_CHAT_HISTORY_PROPERTY_NAME, "")
        user_query = args.get(_USER_QUERY_PROPERTY_NAME, "")
        
        if chat_history and user_query:
            message = f"Context: {chat_history}\n\nQuery: {user_query}"
        elif user_query:
            message = user_query
        else:
            message = "Generate comprehensive wiki documentation based on all code snippets."
        
        # Call the agent directly
        result = await deep_wiki_agent.run(messages=message)
        
        # Extract the response text from the last message
        # result.messages is a list of ChatMessage objects
        # Each message has a 'contents' list containing TextContent objects
        # We need to extract the text from the TextContent objects
        response_text = ""
        if result.messages:
            last_message = result.messages[-1]
            if hasattr(last_message, 'contents') and last_message.contents:
                # Get text from all content items
                response_text = "".join(
                    content.text if hasattr(content, 'text') else str(content)
                    for content in last_message.contents
                )
        
        logging.info(f"MCP: deep_wiki completed successfully")
        return json.dumps({
            "success": True,
            "wiki": response_text,
            "message": "Wiki documentation generated successfully"
        })
        
    except Exception as e:
        logging.error(f"Error in mcp_deep_wiki: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})

# =============================================================================
# COMPREHENSIVE DOCUMENTATION FUNCTIONALITY
# =============================================================================

# MCP tool for generating comprehensive documentation via multi-agent orchestration
# This is accessible to AI assistants via the MCP protocol
@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="generate_comprehensive_documentation",
    description="Generates comprehensive documentation using multiple AI agents working together in sequence. This orchestration creates both detailed wiki documentation AND a complementary code style guide by coordinating the DeepWiki and CodeStyle agents. Use this when you need complete project documentation that includes architecture, API docs, usage examples, AND coding standards. The optional 'userquery' parameter can focus the documentation on specific topics.",
    tool_properties=tool_properties_comprehensive_docs.to_json(),
)
@app.durable_client_input(client_name="client")
async def mcp_generate_comprehensive_documentation(context, client) -> str:
    """
    MCP tool to generate comprehensive documentation using the documentation_orchestration.
    
    This trigger starts a multi-agent orchestration that:
    1. Uses DeepWiki agent to generate comprehensive wiki documentation
    2. Refines the wiki with additional details
    3. Uses CodeStyle agent to generate a complementary style guide
    
    The orchestration coordinates the agents in sequence, sharing context between calls.
    """
    try:
        logging.info("MCP: Starting comprehensive documentation generation via orchestration")
        
        # Parse the context to extract the user query
        mcp_data = json.loads(context)
        args = mcp_data.get("arguments", {})
        user_query = args.get(_USER_QUERY_PROPERTY_NAME, "Generate comprehensive documentation")
        
        # Prepare input for the orchestration
        orchestration_input = {"query": user_query}
        
        # Start the documentation orchestration
        instance_id = await client.start_new(
            orchestration_function_name="documentation_orchestration",
            client_input=orchestration_input
        )
        
        logging.info(f"MCP: Started documentation orchestration with instance_id: {instance_id}")
        
        # Wait for the orchestration to complete
        # Note: For long-running operations, you might want to return the instance_id
        # and let the user poll for status. For now, we'll wait for completion.
        import asyncio
        max_wait_seconds = 300  # 5 minutes timeout
        poll_interval = 2  # Check every 2 seconds
        elapsed = 0
        
        while elapsed < max_wait_seconds:
            status = await client.get_status(instance_id)
            
            if status.runtime_status.name == "Completed":
                logging.info(f"MCP: Orchestration completed successfully")
                return json.dumps({
                    "success": True,
                    "wiki": status.output.get("wiki", ""),
                    "styleGuide": status.output.get("styleGuide", ""),
                    "message": "Comprehensive documentation generated successfully",
                    "instanceId": instance_id
                })
            elif status.runtime_status.name in ["Failed", "Terminated"]:
                logging.error(f"MCP: Orchestration failed with status: {status.runtime_status.name}")
                return json.dumps({
                    "success": False,
                    "error": f"Orchestration failed: {status.runtime_status.name}",
                    "instanceId": instance_id
                })
            
            # Still running, wait and check again
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        # Timeout reached
        logging.warning(f"MCP: Orchestration timed out after {max_wait_seconds} seconds")
        return json.dumps({
            "success": False,
            "error": f"Orchestration timed out after {max_wait_seconds} seconds. Check status at instance ID: {instance_id}",
            "instanceId": instance_id,
            "message": "You can check the orchestration status using the HTTP endpoint"
        })
        
    except Exception as e:
        logging.error(f"Error in mcp_generate_comprehensive_documentation: {str(e)}", exc_info=True)
        return json.dumps({"error": str(e)})

# =============================================================================
# DURABLE AGENT ORCHESTRATIONS
# =============================================================================
# The AgentFunctionApp (imported from agents/durable_agents.py) automatically
# creates HTTP endpoints for direct agent interaction:
#   - POST /api/agents/DeepWikiAgent/run
#   - POST /api/agents/CodeStyleAgent/run
#   - GET /api/health
#
# You can also create orchestrations that use agents via context.get_agent()
# See agents/durable_agents.py for agent definitions
# =============================================================================