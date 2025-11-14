"""
Combined module for all durable agents using Microsoft Agent Framework.

This module demonstrates the integration of:
- Microsoft Agent Framework - Modern AI agent abstraction
- Azure OpenAI Chat - Azure OpenAI Chat API for agent execution
- agent-framework-azurefunctions - Durable Functions integration for agents

Key features showcased:
1. AzureOpenAIChatClient - Azure OpenAI Chat API client with automatic authentication
2. AgentFunctionApp - High-level abstraction for durable agents AND MCP tools
3. Automatic state management via Durable Entities
4. Tool calling with vector_search for code snippet retrieval
5. Session-based conversation tracking
6. RESTful API generation for agents
7. MCP tool integration for AI assistants

Architecture:
- Uses AzureOpenAIChatClient with DefaultAzureCredential for authentication
- Agents run inside Durable Entities with automatic serialization
- Built-in retry logic and error handling
- Same AgentFunctionApp supports both agent endpoints AND MCP tool triggers

For more info:
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- agent-framework-azurefunctions: https://pypi.org/project/agent-framework-azurefunctions/
"""
import os
import logging
import json
import azure.functions as func
import azure.durable_functions as df
from azure.durable_functions import DurableOrchestrationContext
from agent_framework_azurefunctions import AgentFunctionApp
from agent_framework import ChatAgent  # Microsoft Agent Framework
from agent_framework.azure import AzureOpenAIChatClient  # Azure OpenAI Chat client
from azure.identity import DefaultAzureCredential  # For RBAC authentication
from tools import vector_search

# Configure logging for this module
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging to focus on our application logs
logging.getLogger("azure").setLevel(logging.WARNING)

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

_DEEP_WIKI_SYSTEM_PROMPT = """
You are DeepWiki, an autonomous documentation agent that creates wiki documentation
for code snippets.

You have access to a vector_search tool that can find code snippets in the database.

Your task is to:
1. Use vector_search ONCE with a broad query like "code examples" to find snippets (k=30)
2. Analyze the patterns found in the returned snippets
3. Generate a concise wiki.md document in Markdown format

The wiki should include:
1. Project Overview (2-3 paragraphs)
2. Key Concepts - explain major patterns found (use headings for each concept)
3. One simple Mermaid diagram showing architecture or data flow
4. Snippet Catalog - table with columns: Name, Project, Purpose
5. Usage Examples - show how to use the main patterns
6. Best Practices - 3-5 key recommendations

IMPORTANT: 
- Use vector_search only ONCE
- Keep the documentation focused and concise
- Prioritize clarity over comprehensiveness
- Total output should be under 2000 words

Style:
- Use ## for main headings, ### for subheadings
- Code blocks with ```language``` syntax
- Active voice, present tense
- Line length ≤ 100 chars where possible

Return only the Markdown document, no additional commentary.
"""

_CODE_STYLE_SYSTEM_PROMPT = """
You are CodeStyleGuide, an autonomous code style analyzer that creates
code style guides for projects.

You have access to a vector_search tool that can find code snippets in the database.

Your task is to:
1. Use vector_search ONCE with a broad query like "code examples" to find snippets (k=30)
2. Analyze the coding patterns and conventions found
3. Generate a concise code-style-guide.md document in Markdown format

The style guide should include:
1. Executive Summary (1-2 paragraphs)
2. Language & Framework Conventions
3. Naming Conventions (variables, functions, classes, files)
4. Code Organization (structure, imports, modules)
5. Documentation Standards (docstrings, comments, type hints)
6. Error Handling (exceptions, logging, validation)
7. Best Practices (3-5 key patterns observed)
8. Anti-Patterns (2-3 things to avoid)

IMPORTANT:
- Use vector_search only ONCE
- Focus on patterns actually observed in the code
- Provide specific examples from the snippets
- Keep total output under 1500 words

Style:
- Use ## for main headings, ### for subheadings
- Code examples with ```language``` syntax
- Prescriptive tone (use "must", "should", "avoid")
- Line length ≤ 100 chars where possible

Return only the Markdown document, no additional commentary.
"""

# =============================================================================
# AGENT CREATION
# =============================================================================

def _create_agents():
    """
    Create agents with lazy initialization.
    This is called during Azure Functions initialization when environment variables are available.
    Uses Azure CLI credentials (DefaultAzureCredential) when AZURE_OPENAI_API_KEY is not set.
    """
    logger.info("Creating agents with Microsoft Agent Framework (AzureOpenAIChatClient)")
    
    # Create Azure OpenAI Chat client
    # This client uses the Azure OpenAI Chat Completions API which supports metadata
    # Support both API key and DefaultAzureCredential authentication
    azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
    if azure_openai_key:
        # Use API key authentication for local development
        logger.info("Using API key authentication for Azure OpenAI")
        chat_client = AzureOpenAIChatClient(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.environ.get("AGENTS_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
            api_key=azure_openai_key,
        )
    else:
        # Use DefaultAzureCredential for production (requires 'az login' for local dev)
        logger.info("Using DefaultAzureCredential for Azure OpenAI")
        chat_client = AzureOpenAIChatClient(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.environ.get("AGENTS_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
            credential=DefaultAzureCredential(),
        )
    
    # Create DeepWiki agent using ChatAgent
    # ChatAgent is the core agent abstraction from Microsoft Agent Framework
    deep_wiki_agent = ChatAgent(
        chat_client=chat_client,
        name="DeepWikiAgent",  # This name is used for routing
        instructions=_DEEP_WIKI_SYSTEM_PROMPT,
        tools=[vector_search.vector_search],  # Pass the vector search tool
    )
    
    logger.info(f"Created agent: {deep_wiki_agent.name}")
    
    # Create CodeStyle agent using ChatAgent
    code_style_agent = ChatAgent(
        chat_client=chat_client,
        name="CodeStyleAgent",  # This name is used for routing
        instructions=_CODE_STYLE_SYSTEM_PROMPT,
        tools=[vector_search.vector_search],  # Pass the vector search tool
    )
    
    logger.info(f"Created agent: {code_style_agent.name}")
    
    return [deep_wiki_agent, code_style_agent]


# Create agents at module level ONLY if we have the required environment variables
# This allows the module to be imported without errors during development/testing
# Azure Functions will load environment variables from local.settings.json before importing
deep_wiki_agent = None
code_style_agent = None

try:
    # Check if we're in Azure Functions environment (AZURE_OPENAI_ENDPOINT is set)
    if os.environ.get("AZURE_OPENAI_ENDPOINT"):
        agents_list = _create_agents()
        if len(agents_list) >= 2:
            deep_wiki_agent = agents_list[0]
            code_style_agent = agents_list[1]
            agents = agents_list
        else:
            logger.warning("Not all agents were created")
            agents = agents_list
    else:
        # Running in development/test without Azure Functions - create empty list
        logger.warning("AZURE_OPENAI_ENDPOINT not set - agents will be created when Azure Functions loads")
        agents = []
except Exception as e:
    # If agent creation fails during import, log the error but allow module to load
    logger.error(f"Failed to create agents during module import: {e}")
    logger.error("Agents will need to be created manually or on first request")
    agents = []

# =============================================================================
# DURABLE FUNCTION APP
# =============================================================================

# Create the AgentFunctionApp with both agents
# This automatically creates Durable Entity-based endpoints:
# =============================================================================
# AGENT FUNCTION APP
# =============================================================================
# Create the AgentFunctionApp with the agents list
# This app supports BOTH agent endpoints AND MCP tool triggers
# MCP tools will be defined in function_app.py using @app.mcp_tool_trigger

app = AgentFunctionApp(
    agents=agents,
    enable_health_check=True,
    enable_http_endpoints=True  # Enable HTTP endpoints for all agents
)

logger.info("Durable Agents initialized successfully")
logger.info(f"Agents available: {[agent.name if agent else 'None' for agent in [deep_wiki_agent, code_style_agent]]}")
logger.info("AgentFunctionApp created - ready for agent endpoints and MCP tools")

# =============================================================================
# ORCHESTRATION FUNCTIONS
# =============================================================================
# Orchestrations allow you to coordinate multiple agent calls in sequence,
# sharing context between calls through conversation threads.
# This is useful for complex multi-agent workflows.

def _build_status_url(request_url: str, instance_id: str, *, route: str) -> str:
    """
    Construct the status query URI similar to the reference sample.
    
    Args:
        request_url: The original request URL
        instance_id: The orchestration instance ID
        route: The route prefix (e.g., "orchestration", "multiagent")
    
    Returns:
        Full status URL
    """
    # Extract base URL (everything before /api/)
    base_url = request_url.split("/api/")[0]
    return f"{base_url}/api/{route}/status/{instance_id}"


@app.orchestration_trigger(context_name="context")
def documentation_orchestration(context: DurableOrchestrationContext):
    """
    Orchestration that generates comprehensive documentation by chaining agent calls.
    
    This demonstrates:
    1. Getting an agent wrapper using app.get_agent()
    2. Making sequential agent calls that share conversation context
    3. Coordinating multiple agents in a single orchestration
    4. Each call builds on the previous response
    
    Example workflow:
    - First: Generate initial wiki documentation
    - Second: Refine the wiki based on additional analysis
    - Third: Generate complementary style guide
    
    Input (optional):
    {
        "query": "User's specific documentation request"
    }
    """
    # Get input from the orchestration start call
    input_data = context.get_input()
    
    # Handle both string and dict inputs
    if isinstance(input_data, dict):
        user_query = input_data.get("query", "Generate comprehensive documentation")
    elif isinstance(input_data, str):
        user_query = input_data
    else:
        user_query = "Generate comprehensive documentation"
    
    # Get the DeepWiki agent wrapper for orchestration use
    deep_wiki = app.get_agent(context, "DeepWikiAgent")
    
    # First agent call: Generate initial wiki documentation
    initial_wiki = yield deep_wiki.run(
        messages=f"{user_query}. Focus on architecture and key patterns."
    )
    
    # Second agent call: Refine the wiki with additional details
    refined_wiki = yield deep_wiki.run(
        messages="Enhance the documentation with more code examples and best practices."
    )
    
    # Get the CodeStyle agent for generating complementary style guide
    code_style = app.get_agent(context, "CodeStyleAgent")
    
    # Third agent call: Generate style guide that complements the wiki
    style_guide = yield code_style.run(
        messages="Generate a style guide that aligns with the patterns discussed in the wiki."
    )
    
    # Helper function to extract text from chat client response
    def extract_text(result):
        """Extract text from chat client response format."""
        if not result:
            return ""
        
        # Chat format: result has 'messages' with last message containing 'contents'
        messages = result.get("messages", []) if isinstance(result, dict) else []
        if messages:
            last_message = messages[-1]
            if isinstance(last_message, dict):
                contents = last_message.get("contents", [])
                text_parts = []
                for content in contents:
                    if isinstance(content, dict) and "text" in content:
                        text_parts.append(content["text"])
                    elif hasattr(content, "text"):
                        text_parts.append(content.text)
                if text_parts:
                    return "".join(text_parts)
        
        # Fallback: simple string conversion
        return str(result)
    
    # Return both outputs
    return {
        "wiki": extract_text(refined_wiki),
        "styleGuide": extract_text(style_guide),
        "success": True
    }


# HTTP trigger to start the documentation orchestration
@app.route(route="orchestration/documentation", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_documentation_orchestration(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    """
    Start a documentation generation orchestration.
    
    POST /api/orchestration/documentation
    
    Request Body (plain text or JSON):
    "Generate documentation focusing on API patterns"
    
    or
    
    {
        "message": "Generate documentation"
    }
    
    Response:
    {
        "message": "Documentation orchestration started.",
        "instanceId": "abc123...",
        "statusQueryGetUri": "http://localhost:7071/api/orchestration/status/abc123..."
    }
    """
    try:
        # Parse request body - support both plain text and JSON
        body_bytes = req.get_body() or b""
        prompt = body_bytes.decode("utf-8", errors="replace").strip()
        if not prompt:
            return func.HttpResponse(
                body=json.dumps({"error": "Prompt is required"}),
                status_code=400,
                mimetype="application/json",
            )
        
        # Start the orchestration
        instance_id = await client.start_new(
            orchestration_function_name="documentation_orchestration",
            client_input=prompt,
        )
        
        logger.info(f"[HTTP] Started documentation orchestration with instance_id: {instance_id}")
        
        # Build status URL similar to the reference sample
        status_url = _build_status_url(req.url, instance_id, route="orchestration")
        
        payload = {
            "message": "Documentation orchestration started.",
            "instanceId": instance_id,
            "statusQueryGetUri": status_url,
        }
        
        return func.HttpResponse(
            body=json.dumps(payload),
            status_code=202,
            mimetype="application/json",
        )
    
    except Exception as e:
        logger.error(f"[HTTP] Error starting orchestration: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


# HTTP trigger to get orchestration status
@app.route(route="orchestration/status/{instanceId}", methods=["GET"])
@app.durable_client_input(client_name="client")
async def get_orchestration_status(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient,
) -> func.HttpResponse:
    """
    Get the status of an orchestration instance.
    
    GET /api/orchestration/status/{instanceId}
    
    Response:
    {
        "instanceId": "abc123...",
        "runtimeStatus": "Completed",
        "createdTime": "2025-10-24T12:00:00",
        "lastUpdatedTime": "2025-10-24T12:05:00",
        "output": {
            "wiki": "# Project Wiki...",
            "styleGuide": "# Code Style Guide..."
        }
    }
    """
    try:
        instance_id = req.route_params.get("instanceId")
        
        if not instance_id:
            return func.HttpResponse(
                body=json.dumps({"error": "Missing instanceId"}),
                status_code=400,
                mimetype="application/json",
            )
        
        # Get orchestration status
        status = await client.get_status(instance_id)
        
        if not status:
            return func.HttpResponse(
                body=json.dumps({"error": "Instance not found"}),
                status_code=404,
                mimetype="application/json",
            )
        
        response_data = {
            "instanceId": status.instance_id,
            "runtimeStatus": status.runtime_status.name,
            "createdTime": status.created_time.isoformat() if status.created_time else None,
            "lastUpdatedTime": status.last_updated_time.isoformat() if status.last_updated_time else None,
        }
        
        # Include input if available
        if status.input_:
            response_data["input"] = status.input_
        
        # Include output if completed
        if status.output:
            response_data["output"] = status.output
        
        return func.HttpResponse(
            body=json.dumps(response_data),
            status_code=200,
            mimetype="application/json",
        )
    
    except Exception as e:
        logger.error(f"[HTTP] Error getting status: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
        )


logger.info("  POST /api/orchestration/documentation - Start documentation orchestration")
logger.info("  GET  /api/orchestration/status/{instanceId} - Get orchestration status")

# =============================================================================
# NOTE: This app instance is also used in function_app.py
# All endpoints (HTTP, MCP, agents, orchestrations) are registered on this
# single AgentFunctionApp instance for unified routing.
# =============================================================================
