# Module for generating a code style guide using Azure AI Agents service.
# This module:
# - Defines the system prompt and instructions for the CodeStyleSynthesizer agent
# - Sets up Azure AI Project Client and authentication
# - Registers the vector_search tool for retrieving code examples
# - Manages the lifecycle of the AI agent, thread, messages, and run
# - Returns a comprehensive Markdown style guide based on code examples
import os
import logging
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ToolSet
from azure.identity import DefaultAzureCredential
from agents.tools import vector_search

# Configure logging for this module
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging to focus on our application logs
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.ai.projects").setLevel(logging.WARNING)

# System prompt for the code style synthesizer agent
# This prompt defines the agent's personality, capabilities, and constraints
_CODE_STYLE_SYSTEM_PROMPT = """
You are CodeStyleSynthesizer, an autonomous agent that produces a code style guide.

You have access to a vector_search tool that can find relevant code snippets in the database.

Your task is to:
1. Perform a SINGLE vector search to find relevant code snippets that demonstrate various coding patterns
2. Analyze ALL patterns and conventions found in the code
3. Generate a comprehensive code style guide in Markdown format

The style guide should cover:
- Naming conventions
- Code organization
- Documentation standards
- Error handling
- Logging practices
- Any other relevant style aspects

For each section, provide:
- Clear, concise rules
- Examples from actual code snippets
- Best practices and recommendations

IMPORTANT: Use vector_search only ONCE to get a comprehensive set of examples. Do not make multiple searches.

Return only the final Markdown document, no additional commentary.
"""

async def generate_code_style(chat_history: str = "", user_query: str = "") -> str:
    """
    Generates a code style guide using an AI agent.
    
    This function:
    1. Creates an AI agent with the CodeStyleSynthesizer personality
    2. Provides the agent with a vector search tool to find code examples
    3. Manages the agent's execution and tool calls
    4. Returns the generated style guide
    
    The agent uses Azure AI Agents service to:
    - Understand the task through the system prompt
    - Use the vector search tool to find relevant code
    - Generate a comprehensive style guide based on the code patterns
    
    Args:
        chat_history: The chat history or session for context
        user_query: The user's query for code style analysis
    
    Returns:
        str: The generated code style guide in Markdown format
    """
    try:
        # Log input parameters
        logger.info("Starting code style generation with:")
        logger.info("Chat history length: %d characters", len(chat_history))
        if chat_history:
            logger.info("Chat history preview: %s", chat_history[:200] + "..." if len(chat_history) > 200 else chat_history)
        logger.info("User query: %s", user_query)
        
        # Log the system prompt for debugging and transparency
        logger.info("System prompt:\n%s", _CODE_STYLE_SYSTEM_PROMPT)
        
        # Create an Azure credential for authentication
        logger.info("Initializing Azure authentication")
        credential = DefaultAzureCredential()
        
        # Connect to the Azure AI Project that hosts our agent
        logger.info("Connecting to Azure AI Project")
        project_client = AIProjectClient(
            endpoint=os.environ["PROJECT_ENDPOINT"],
            credential=credential
        )
        
        with project_client:
            # Create the vector search tool that the agent will use
            logger.info("Setting up vector search tool")
            functions = FunctionTool({vector_search.vector_search})
            toolset = ToolSet()
            toolset.add(functions)
            
            # Enable automatic function calls
            project_client.agents.enable_auto_function_calls(toolset)
            
            # Create the agent with its personality and tools
            logger.info("Creating CodeStyleSynthesizer agent with model: %s", os.environ["AGENTS_MODEL_DEPLOYMENT_NAME"])
            agent = project_client.agents.create_agent(
                name="CodeStyleSynthesizer",
                instructions=_CODE_STYLE_SYSTEM_PROMPT,
                toolset=toolset,
                model=os.environ["AGENTS_MODEL_DEPLOYMENT_NAME"]
            )
            logger.info("Created agent: %s with tool: vector_search", agent.name)
            
            # Create a conversation thread for the agent
            logger.info("Creating conversation thread")
            thread = project_client.agents.threads.create()
            
            # Add chat history if provided
            if chat_history:
                logger.info("Adding chat history to thread")
                project_client.agents.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=chat_history
                )
            
            # Add the user's query or default message
            final_query = user_query if user_query else "Generate a code style guide."
            logger.info("Adding user query to thread: %s", final_query)
            project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=final_query
            )
            
            # Start the agent's execution and process it automatically
            logger.info("Starting agent execution")
            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id
            )
            logger.info("Agent run completed with status: %s", run.status)
            
            # Check for failure
            if run.status == "failed":
                logger.error("Agent run failed with error: %s", run.last_error)
                raise Exception(f"Agent run failed: {run.last_error}")
            
            # Get the final response from the agent
            logger.info("Retrieving final response from agent")
            messages = project_client.agents.messages.list(thread_id=thread.id)
            
            # Find the latest assistant message
            response = None
            for message in messages:
                if message.role == "assistant":
                    # Get the text content from the message
                    if message.content and len(message.content) > 0:
                        response = str(message.content[0].text.value)
                        break
            
            if not response:
                raise Exception("No response generated by the agent")
            
            logger.info("Code style guide generated by %s. Response length: %d", agent.name, len(response))
            return response
                
    except Exception as e:
        logger.error("Code style generation failed with error: %s", str(e), exc_info=True)
        raise
