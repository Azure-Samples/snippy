# Step 2: Code Review - Understanding MCP Tools and AI Agents with Azure Functions

As *azd provision* sets up your cloud resources in the background, you'll explore how **Azure Functions** power AI-enabled tools and agent orchestration.

## What You'll Learn

Azure Functions provides a serverless platform for building AI-integrated microservices. You'll review two key integration patterns:

1. **Azure Functions as MCP Tools for AI Agents:**
   See how Azure Functions become discoverable tools for AI agents like GitHub Copilot. The MCP tool trigger makes your function directly usable by any MCP-compatible client without custom integration code.

2. **Azure Functions with Durable AI Agents:**
   Explore how Azure Functions use the agent-framework-azurefunctions library to create durable AI agents. These agents persist state automatically and can use other functions (like vector search) as tools.

**Key Azure Technologies:**

- **Azure Functions**: Serverless compute for AI tools and agent interactions
- **MCP Tool Trigger** (*@app.mcp_tool_trigger*): Exposes functions as discoverable MCP tools
- **Embeddings Input Binding** (*@app.embeddings_input*): Automatically generates vector embeddings
- **Azure Cosmos DB with Vector Search**: Stores snippets and embeddings for semantic retrieval
- **agent-framework-azurefunctions**: Enables durable AI agents with automatic state management

---

## 2.1 Review: Tool Schema Definition

**Target File:** Open ***src/function_app.py*** in VS Code

1. Navigate to the **TOOL PROPERTY DEFINITIONS** section (around line 65)

2. **Examine how tool properties are defined:**

    ```python
    tool_properties_save_snippets = ToolPropertyList(
        ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "A unique name or identifier for the code snippet..."),
        ToolProperty(_PROJECT_ID_PROPERTY_NAME, "string", "An identifier for a project to associate this snippet with..."),
        ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The actual code or text content of the snippet..."),
    )
    ```

    > **What This Does:**
    >
    > - `ToolPropertyList` is a helper class that creates a list of tool properties
    > - Each `ToolProperty` defines a parameter with: name, type, and description
    > - The descriptions are detailed natural language that helps AI agents understand what each parameter is for
    > - Call `.to_json()` to serialize this schema for the MCP protocol

---

## 2.2 Review: MCP Tool Trigger Binding

1. Scroll to the *mcp_save_snippet* function (around line 174)

2. **Examine the MCP tool trigger decorator:**

    ```python
    @app.mcp_tool_trigger(
        arg_name="context",
        tool_name="save_snippet",
        description="Saves a given code snippet. It can take a snippet name, the snippet content, and an optional project ID. Embeddings are generated for the content to enable semantic search. The LLM should provide 'snippetname' and 'snippet' when intending to save.",
        tool_properties=tool_properties_save_snippets.to_json(),
    )
    ```

    > **What This Does:**
    >
    > - The `@app.mcp_tool_trigger` decorator registers this function as an MCP tool
    > - `arg_name="context"` - the parameter that receives MCP data as a JSON string
    > - `tool_name="save_snippet"` - how AI assistants will refer to this tool
    > - `description` - explains to the AI what this tool does
    > - `tool_properties` - the schema (from section 2.1) serialized as JSON
    > - When deployed, Azure Functions automatically exposes an MCP endpoint that AI assistants can discover

---

## 2.3 Review: Embeddings Input Binding

1. Look at the decorator chain above *http_save_snippet* (line 104) and *mcp_save_snippet* (line 180)

2. **Examine the embeddings input binding:**

    **For HTTP endpoint:**

    ```python
    @app.embeddings_input(arg_name="embeddings", input="{code}", input_type="rawText", embeddings_model="%EMBEDDING_MODEL_DEPLOYMENT_NAME%")
    ```

    **For MCP endpoint:**

    ```python
    @app.embeddings_input(arg_name="embeddings", input="{arguments.snippet}", input_type="rawText", embeddings_model="%EMBEDDING_MODEL_DEPLOYMENT_NAME%")
    ```

    > **What This Does:**
    >
    > - This binding automatically calls Azure OpenAI **before** your function runs
    > - It extracts text from the input and generates vector embeddings
    > - Notice the path difference:
    >   - HTTP: `{code}` references the JSON request body field
    >   - MCP: `{arguments.snippet}` references the MCP context structure
    > - The resulting embedding is passed to your function as the `embeddings` parameter
    > - Inside the function, you parse the JSON string to extract the vector array

---

## 2.4 Review: Durable AI Agents with Microsoft Agent Framework

**Target File:** Open ***src/durable_agents.py***

This application uses the **Microsoft Agent Framework** with **agent-framework-azurefunctions** to create stateful AI agents.

1. **Azure OpenAI Chat Client** (around line 135):

    ```python
    # Support both API key and DefaultAzureCredential authentication
    azure_openai_key = os.environ.get("AZURE_OPENAI_KEY")
    if azure_openai_key:
        # Use API key authentication for local development
        chat_client = AzureOpenAIChatClient(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.environ.get("AGENTS_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
            api_key=azure_openai_key,
        )
    else:
        # Use DefaultAzureCredential for production
        chat_client = AzureOpenAIChatClient(
            endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.environ.get("AGENTS_MODEL_DEPLOYMENT_NAME", "gpt-4o-mini"),
            credential=DefaultAzureCredential(),
        )
    ```

    > **AzureOpenAIChatClient:**
    >
    > - Uses the Azure OpenAI Chat Completions API
    > - Supports both API key and managed identity authentication
    > - Configured with the model deployment name from environment variables

2. **Agent Definition with ChatAgent** (around line 155):

    ```python
    deep_wiki_agent = ChatAgent(
        chat_client=chat_client,
        name="DeepWikiAgent",
        instructions=_DEEP_WIKI_SYSTEM_PROMPT,
        tools=[vector_search.vector_search],
    )
    
    code_style_agent = ChatAgent(
        chat_client=chat_client,
        name="CodeStyleAgent",
        instructions=_CODE_STYLE_SYSTEM_PROMPT,
        tools=[vector_search.vector_search],
    )
    ```

    > **ChatAgent (Microsoft Agent Framework):**
    >
    > - `ChatAgent` is the core agent abstraction from Microsoft Agent Framework
    > - `chat_client` - The AzureOpenAIChatClient that executes the agent
    > - `name` - Used for routing and identification
    > - `instructions` - The system prompt that defines agent behavior
    > - `tools` - List of Python functions the agent can call (e.g., `vector_search.vector_search`)
    > - The framework automatically discovers tool schemas from function signatures and docstrings

3. **AgentFunctionApp** (around line 217):

    ```python
    app = AgentFunctionApp(
        agents=agents,
        enable_health_check=True,
        enable_http_endpoints=True  # Enable HTTP endpoints for all agents
    )
    ```

    > **Auto-Generated Endpoints:**
    >
    > `AgentFunctionApp` extends Azure Functions and automatically creates:
    > - `POST /api/agents/DeepWikiAgent/run` - Execute the DeepWiki agent
    > - `POST /api/agents/CodeStyleAgent/run` - Execute the CodeStyle agent
    > - `GET /api/agents/DeepWikiAgent/{sessionId}` - Get conversation state
    > - `GET /api/agents/CodeStyleAgent/{sessionId}` - Get conversation state
    > - `GET /api/health` - Health check endpoint
    >
    > State is automatically persisted using Durable Entities, so conversation history is maintained across calls.

4. **Multi-Agent Orchestration** (around line 251):

    ```python
    @app.orchestration_trigger(context_name="context")
    def documentation_orchestration(context: DurableOrchestrationContext):
        """Orchestration that chains multiple agent calls."""
        
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
        
        return {
            "wiki": extract_text(refined_wiki),
            "styleGuide": extract_text(style_guide),
            "success": True
        }
    ```

    > **Orchestration Pattern:**
    >
    > - Use `get_agent(context, name)` to get an agent wrapper for orchestration
    > - `yield agent.run(...)` executes the agent as a Durable Functions activity
    > - Sequential calls to the same agent automatically share conversation context
    > - Different agents can be coordinated in sequence
    > - All state is automatically persisted by Durable Functions

---

**Key Differences from Direct Azure AI Agents Service:**

| Aspect | This Implementation | Direct Azure AI Agents Service |
|--------|---------------------|--------------------------------|
| **Agent Class** | `ChatAgent` (Microsoft Agent Framework) | `AIProjectClient.agents.create_agent()` |
| **Client** | `AzureOpenAIChatClient` | `AIProjectClient` |
| **Tool Discovery** | Automatic from Python functions | Manual tool definitions |
| **State Management** | Automatic via Durable Entities | Manual via threads |
| **Lifecycle** | Simple `agent.run()` | Manual create/run/poll loop |
| **HTTP Endpoints** | Auto-generated by `AgentFunctionApp` | Must build manually |
| **Orchestration** | Built-in via Durable Functions | Must implement manually |

---

## 2.5 Review: Vector Search Tool

**Target File:** Open ***src/tools/vector_search.py***

The `vector_search` function demonstrates how agents use tools. It's a standard Python async function that the agent framework automatically discovers and makes available to agents:

```python
async def vector_search(query: str, k: int = 30, project_id: str = "default-project") -> str:
    """
    Performs vector similarity search on code snippets.
    
    Args:
        query: The search query text (plain language or code fragment)
        k: Number of top matches to return
        project_id: The project ID to scope the search
        
    Returns:
        JSON string of matching snippets with their IDs, code, and similarity scores
    """
```

> **How It Works:**
>
> - Standard Python async function with type hints and docstring
> - Microsoft Agent Framework automatically discovers it from the signature
> - When an agent needs to search snippets, it calls this function
> - Generates embeddings for the query using Azure OpenAI SDK directly
> - Queries Cosmos DB vector index for similar snippets using cosine distance
> - Returns results as JSON string back to the agent
>
> This is part of the RAG (Retrieval-Augmented Generation) pattern: retrieve relevant code snippets, then use them to generate accurate, grounded responses. This enables semantic search where agents can find relevant code even without exact keyword matches.

---

## Next Steps

You've reviewed the core implementation patterns. In the following sections, you'll:

1. Run the functions locally to see these patterns in action
2. Test with REST Client and GitHub Copilot
3. Deploy to Azure and connect to the cloud MCP endpoint
