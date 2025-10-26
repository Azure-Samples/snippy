"""
Combined module for all durable agents using Microsoft Agent Framework.

This module demonstrates the integration of:
- Microsoft Agent Framework - Modern AI agent abstraction with ChatAgent
- Azure OpenAI Responses - Latest OpenAI Responses API for agent execution
- agent-framework-azurefunctions - Durable Functions integration for agents

Key features showcased:
1. ChatAgent - Microsoft's unified agent abstraction from agent-framework
2. AzureOpenAIResponsesClient - Azure OpenAI Responses API client
3. AgentFunctionApp - High-level abstraction for durable agents
4. Automatic state management via Durable Entities
5. Tool calling with vector_search for code snippet retrieval
6. Session-based conversation tracking
7. RESTful API generation for both DeepWiki and CodeStyle agents

Architecture:
- Uses Microsoft Agent Framework's ChatAgent as the core agent abstraction
- AzureOpenAIResponsesClient provides Azure OpenAI Responses API integration
- Agents run inside Durable Entities with automatic serialization
- Built-in retry logic and error handling
- Optional orchestrations for multi-agent workflows (see documentation_orchestration)

Endpoints automatically created by AgentFunctionApp:
- POST /api/agents/DeepWikiAgent/run - Generate wiki documentation
- POST /api/agents/CodeStyleAgent/run - Generate code style guide
- GET /api/agents/{AgentName}/{sessionId} - Retrieve conversation history
- GET /api/health - Health check endpoint

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
from durableagent import AgentFunctionApp
from agent_framework import ChatAgent  # Microsoft Agent Framework
from agent_framework.azure import AzureOpenAIResponsesClient  # Azure OpenAI Responses client
from azure.identity import DefaultAzureCredential
from agents.tools import vector_search

# Configure logging for this module
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging to focus on our application logs
logging.getLogger("azure").setLevel(logging.WARNING)

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

_DEEP_WIKI_SYSTEM_PROMPT = """
You are DeepWiki, an autonomous documentation agent whose single task is to
produce a complete wiki.md that explains every important aspect of the
saved code snippets in this project.

You have access to a vector_search tool that can find relevant code snippets in the database.

Your task is to:
1. Perform a SINGLE vector search to find relevant code snippets that demonstrate various coding patterns
2. Analyze ALL patterns and conventions found in the code
3. Generate a comprehensive wiki.md document in Markdown format

The wiki should include:
1. A concise project overview
2. Explanation of every major concept found in the snippets (algorithms, APIs,
   design patterns, domain entities, error handling, logging, etc.)
3. One or more Mermaid diagrams that visualise:
   - The system architecture (how components interact)
   - The data flow between components
   - The call graph of major functions
   - The class hierarchy if object-oriented code is present
   - The state machine if stateful components exist
   Choose the most relevant diagram types based on the code patterns found.
4. A Snippet Catalog table listing each snippet id, language, and one-line purpose
5. Step-by-step walkthroughs that show how to use the code end-to-end
6. Best practices, anti-patterns, and open TODOs
7. A Further Reading section

IMPORTANT: Use vector_search only ONCE to get a comprehensive set of examples. Do not make multiple searches.

Style Rules:
- Use hyphens (-) instead of em dashes
- Headings with #, ##, etc.
- Code fenced with triple back-ticks; Mermaid diagrams fenced with ```mermaid``` tags
- Keep line length ≤ 120 chars
- Active voice, present tense, developer-friendly tone
- For Mermaid diagrams:
  - Use clear, descriptive node names
  - Include arrows with labels to show relationships
  - Group related components using subgraphs
  - Use consistent styling for similar elements
  - Add a title to each diagram
  - Keep diagrams focused and readable

Return only the final Markdown document, no additional commentary.
"""

_CODE_STYLE_SYSTEM_PROMPT = """
You are CodeStyleGuide, an autonomous code style analyzer whose task is to
produce a comprehensive code-style-guide.md that documents the coding standards
and conventions used in the saved code snippets.

You have access to a vector_search tool that can find relevant code snippets in the database.

Your task is to:
1. Perform a SINGLE vector search to find representative code snippets
2. Analyze ALL coding patterns, conventions, and styles found
3. Generate a comprehensive code-style-guide.md document in Markdown format

The style guide should include:
1. Executive Summary - Brief overview of the coding philosophy
2. Language & Framework Conventions - Language-specific patterns observed
3. Naming Conventions:
   - Variables, functions, classes, constants
   - File and directory naming
4. Code Organization:
   - Project structure
   - Module organization
   - Import statements
5. Documentation Standards:
   - Docstring format and requirements
   - Comment style and usage
   - Type hints and annotations
6. Error Handling:
   - Exception handling patterns
   - Logging conventions
   - Error reporting standards
7. Best Practices & Anti-Patterns:
   - Recommended patterns found in the codebase
   - Anti-patterns to avoid
8. Code Examples:
   - Good examples from the snippets
   - Before/after comparisons where relevant

IMPORTANT: Use vector_search only ONCE to get a comprehensive set of examples. Do not make multiple searches.

Style Rules:
- Use hyphens (-) instead of em dashes
- Headings with #, ##, etc.
- Code fenced with triple back-ticks and language identifier
- Keep line length ≤ 120 chars
- Active voice, present tense, prescriptive tone
- Include specific examples from the codebase

Return only the final Markdown document, no additional commentary.
"""

# =============================================================================
# AGENT CREATION
# =============================================================================

logger.info("Creating agents with Microsoft Agent Framework (AzureOpenAIResponsesClient)")

# Create Azure OpenAI Responses client
# This client uses the Azure OpenAI Responses API
# Support both API key and DefaultAzureCredential authentication
azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
if azure_openai_key:
    # Use API key authentication for local development
    logger.info("Using API key authentication for Azure OpenAI")
    responses_client = AzureOpenAIResponsesClient(
        endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.environ.get("AGENTS_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
        api_key=azure_openai_key,
    )
else:
    # Use DefaultAzureCredential for production (requires 'az login' for local dev)
    logger.info("Using DefaultAzureCredential for Azure OpenAI")
    responses_client = AzureOpenAIResponsesClient(
        endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.environ.get("AGENTS_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
        credential=DefaultAzureCredential(),
    )

# Create DeepWiki agent using ChatAgent
# ChatAgent is the core agent abstraction from Microsoft Agent Framework
deep_wiki_agent = ChatAgent(
    chat_client=responses_client,
    name="DeepWikiAgent",  # This name is used for routing
    instructions=_DEEP_WIKI_SYSTEM_PROMPT,
    tools=[vector_search.vector_search],  # Pass the vector search tool
)

logger.info(f"Created agent: {deep_wiki_agent.name}")

# Create CodeStyle agent using ChatAgent
code_style_agent = ChatAgent(
    chat_client=responses_client,
    name="CodeStyleAgent",  # This name is used for routing
    instructions=_CODE_STYLE_SYSTEM_PROMPT,
    tools=[vector_search.vector_search],  # Pass the vector search tool
)

logger.info(f"Created agent: {code_style_agent.name}")

# =============================================================================
# DURABLE FUNCTION APP
# =============================================================================

# Create the AgentFunctionApp with both agents
# This automatically creates Durable Entity-based endpoints:
#
# DeepWiki Agent:
# 1. POST /api/agents/DeepWikiAgent/run - Send messages to the agent
#    Request: {"message": "Generate wiki", "sessionId": "user-123"}
#    Response: {"response": "...", "sessionId": "user-123", "status": "success", "message_count": 1}
# 
# 2. GET /api/agents/DeepWikiAgent/{sessionId} - Retrieve conversation state
#    Response: {"message_count": X, "conversation_history": [...], "last_response": "..."}
#
# CodeStyle Agent:
# 1. POST /api/agents/CodeStyleAgent/run - Send messages to the agent
#    Request: {"message": "Generate style guide", "sessionId": "user-456"}
#    Response: {"response": "...", "sessionId": "user-456", "status": "success", "message_count": 1}
# 
# 2. GET /api/agents/CodeStyleAgent/{sessionId} - Retrieve conversation state
#    Response: {"message_count": X, "conversation_history": [...], "last_response": "..."}
#
# Health Check:
# 3. GET /api/health - Health check
#    Response: {"status": "healthy", "agents": [{"name": "DeepWikiAgent", ...}, {"name": "CodeStyleAgent", ...}]}

app = AgentFunctionApp(
    agents=[deep_wiki_agent, code_style_agent],
    enable_health_check=True  # Enables /api/health endpoint
)

logger.info("Durable Agents initialized successfully")
logger.info("Available endpoints:")
logger.info("  POST /api/agents/DeepWikiAgent/run")
logger.info("  GET  /api/agents/DeepWikiAgent/{sessionId}")
logger.info("  POST /api/agents/CodeStyleAgent/run")
logger.info("  GET  /api/agents/CodeStyleAgent/{sessionId}")
logger.info("  GET  /api/health")

# =============================================================================
# ORCHESTRATION FUNCTIONS
# =============================================================================
# Orchestrations allow you to coordinate multiple agent calls in sequence,
# sharing context between calls through conversation threads.
# This is useful for complex multi-agent workflows.

@app.orchestration_trigger(context_name="context")
def documentation_orchestration(context: DurableOrchestrationContext):
    """
    Orchestration that generates comprehensive documentation by chaining agent calls.
    
    This demonstrates:
    1. Getting an agent wrapper using context.get_agent()
    2. Creating a new conversation thread
    3. Making sequential agent calls with shared thread context
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
    user_query = input_data.get("query", "Generate comprehensive documentation") if input_data else "Generate comprehensive documentation"
    
    # Get the DeepWiki agent wrapper for orchestration use
    deep_wiki = context.get_agent("DeepWikiAgent")
    
    # Create a new conversation thread for the wiki generation
    # Note: get_new_thread() is NOT a task, so don't yield it
    wiki_thread = deep_wiki.get_new_thread()
    
    # First agent call: Generate initial wiki documentation
    initial_wiki = yield deep_wiki.run(
        messages=f"{user_query}. Focus on architecture and key patterns.",
        thread=wiki_thread
    )
    
    # Second agent call: Refine the wiki with additional details
    # Using the same thread maintains conversation context
    refined_wiki = yield deep_wiki.run(
        messages="Enhance the documentation with more code examples and best practices.",
        thread=wiki_thread
    )
    
    # Get the CodeStyle agent for generating complementary style guide
    code_style = context.get_agent("CodeStyleAgent")
    style_thread = code_style.get_new_thread()
    
    # Third agent call: Generate style guide that complements the wiki
    style_guide = yield code_style.run(
        messages="Generate a style guide that aligns with the patterns discussed in the wiki.",
        thread=style_thread
    )
    
    # Return both outputs
    return {
        "wiki": refined_wiki.get("response", ""),
        "styleGuide": style_guide.get("response", ""),
        "success": True
    }


# HTTP trigger to start the documentation orchestration
@app.route(route="orchestration/documentation", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_documentation_orchestration(req: func.HttpRequest, client):
    """
    Start a documentation generation orchestration.
    
    POST /api/orchestration/documentation
    
    Request Body (optional):
    {
        "query": "Generate documentation focusing on API patterns"
    }
    
    Response:
    {
        "message": "Documentation orchestration started.",
        "instanceId": "abc123...",
        "statusQueryGetUri": "http://localhost:7071/api/orchestration/status/abc123..."
    }
    """
    try:
        # Parse request body if provided
        input_data = None
        try:
            req_body = req.get_json()
            if req_body:
                input_data = req_body
        except ValueError:
            pass
        
        # Start the orchestration
        instance_id = await client.start_new(
            orchestration_function_name="documentation_orchestration",
            client_input=input_data
        )
        
        logger.info(f"[HTTP] Started documentation orchestration with instance_id: {instance_id}")
        
        # Build status URL - extract base URL (everything before /api/)
        base_url = req.url.split("/api/")[0]
        status_url = f"{base_url}/api/orchestration/status/{instance_id}"
        
        return func.HttpResponse(
            body=json.dumps({
                "message": "Documentation orchestration started.",
                "instanceId": instance_id,
                "statusQueryGetUri": status_url
            }),
            status_code=202,
            mimetype="application/json"
        )
    
    except Exception as e:
        logger.error(f"[HTTP] Error starting orchestration: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


# HTTP trigger to get orchestration status
@app.route(route="orchestration/status/{instanceId}", methods=["GET"])
@app.durable_client_input(client_name="client")
async def get_orchestration_status(req: func.HttpRequest, client: df.DurableOrchestrationClient):
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
            "styleGuide": "# Code Style Guide...",
            "success": true
        }
    }
    """
    try:
        instance_id = req.route_params.get("instanceId")
        
        if not instance_id:
            return func.HttpResponse(
                body=json.dumps({"error": "Missing instanceId"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get orchestration status
        status = await client.get_status(instance_id)
        
        if not status:
            return func.HttpResponse(
                body=json.dumps({"error": "Instance not found"}),
                status_code=404,
                mimetype="application/json"
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
            mimetype="application/json"
        )
    
    except Exception as e:
        logger.error(f"[HTTP] Error getting status: {e}", exc_info=True)
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json"
        )


logger.info("  POST /api/orchestration/documentation - Start documentation orchestration")
logger.info("  GET  /api/orchestration/status/{instanceId} - Get orchestration status")

# =============================================================================
# NOTE: Snippet CRUD endpoints are defined in function_app.py
# They use a separate FunctionApp instance for backwards compatibility
# =============================================================================
