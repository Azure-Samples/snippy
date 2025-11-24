# Snippy Tutorial: Building an AI-Enhanced Code Snippet Manager

This tutorial guides you through building *Snippy*, an intelligent code snippet manager using Azure Functions. You'll save and retrieve code snippets in Azure Cosmos DB with vector search enabled, using Azure OpenAI embeddings to capture semantic meaning. You'll also create AI agents that generate documentation and coding standards from your snippets.

The key innovation is exposing your Azure Functions as **MCP (Model Context Protocol) Tools** that AI assistants like GitHub Copilot can discover and invoke directly.

You'll implement both patterns:

- Azure Functions as consumable tools for AI agents
- Azure Functions that create and orchestrate AI agents

This dual approach demonstrates how serverless functions can seamlessly integrate with modern AI workflows through standard protocols.

![Snippy Architecture](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/Snippy-Architecture-V2.png)

---

## Prerequisites

Before starting this tutorial, ensure you have the following installed and configured on your local machine:

### Required Software

- **Visual Studio Code** - Your primary development environment
- **Python 3.11 or 3.12**
- **uv** package manager (faster alternative to pip) - Install with:
  - **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
  - **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **Git** for source control
- **Azure CLI** for managing Azure resources - [Installation guide](https://learn.microsoft.com/cli/azure/install-azure-cli)
- **Azure Functions Core Tools v4** - [Installation guide](https://learn.microsoft.com/azure/azure-functions/functions-run-local)
- **Azure Developer CLI (azd)** - [Installation guide](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- **Docker Desktop** for the Durable Task emulator and Azurite support

### Azure Account

- An active Azure subscription with permissions to create resources
- GitHub account with access to GitHub Copilot

### Knowledge Requirements

- Basic understanding of Python
- Familiarity with Azure Functions concepts
- Understanding of REST APIs
- Basic knowledge of Git and command-line tools

---

## Step 1: Set Up Azure Resources

You'll use the Azure Developer CLI (azd) to provision all necessary Azure resources for Snippy. This process takes several minutes (5-10) and will run in the background.

### 1.1 Clone the Repository

``` text
git clone https://github.com/Azure-Samples/snippy.git
cd snippy
code .
```

VS Code will open the **snippy** folder with the source code and assets for the tutorial.

### 1.2 Set Up GitHub Copilot

This tutorial requires GitHub Copilot with access for MCP tool integration.

1. **Verify GitHub Copilot is installed:**
   - In VS Code, check for the GitHub Copilot icon in the Activity Bar (left sidebar)
   - If not installed, install the **GitHub Copilot** and **GitHub Copilot Chat** extensions from the VS Code marketplace

2. **Sign in to GitHub Copilot** (if not already signed in):
   - Click the **account icon** (bottom left) → **Sign in to use GitHub Copilot**
   - Follow the prompts to authenticate with your GitHub account
   - Authorize VS Code to access your GitHub account when prompted

3. **Configure the model:**
   - Open the **GitHub Copilot Chat** window (**Ctrl+Alt+I** or **Cmd+Alt+I**)
   - Click the model selector at the top of the chat panel
   - Select **Claude Sonnet 4.5** from the available models

### 1.3 Provision Azure Resources

Now you'll use azd to provision all necessary Azure resources.

1. Open your terminal inside VS Code (*View → Terminal*) and ensure you are in the *snippy* root directory

   ![VS Code Terminal](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-VS-Terminal.png)

2. **Login to Azure:**

   ```text
   azd auth login
   ```

   Follow the authentication prompts in your browser.

3. **Set up the azd Environment:**

   An azd environment stores configuration details like subscription ID and location. Create a new environment with a unique suffix (replace `<unique-suffix>` with your own identifier, e.g., your initials and a random number like `jd4792`):

   ```text
   azd env new snippymcplab-<unique-suffix> --subscription <your-subscription-id>
   ```

   > **Note**: To find your subscription ID, run `az account list --output table` and use the subscription ID from the output.

4. **Set the name suffix for Azure resources:**

   The name suffix will be added at the end of the resources deployed to Azure:

   ```text
   azd env set NAME_SUFFIX <unique-suffix>
   ```

5. **Provision and Deploy Resources:**

   Run the following command. This reads the infrastructure definition (*infra* folder, *main.bicep*) and begins creating the resources in Azure:

   ```text
   azd provision
   ```

   If prompted, select a location from the terminal to deploy the Azure resources.

   **Do not wait for it to complete.** It will run in the background. Proceed immediately to the next step while it runs.

   > **What This Provisions:**
   > - Azure Function App (using the scalable Flex Consumption plan)
   > - Azure Storage Account (for Functions operations and state)
   > - Azure Cosmos DB for NoSQL (pre-configured for vector search)
   > - Azure AI Services (with *gpt-4o-mini* and *text-embedding-3-small* models deployed)
   > - Microsoft Foundry resources (Foundry projects)
   > - Azure Log Analytics & Application Insights (for monitoring)
   > - Durable Task Scheduler (for workflow orchestration)
   > - Managed Identity (for secure access to Azure resources)

   > **Note**: These resources are created within a new resource group named **rg-snippymcplab-<unique-suffix>**. You will deploy your application code to the Function App later using *azd deploy*.

**Proceed to code review exercises while provisioning takes place**

> **Important**: Ensure you can easily access the terminal running *azd provision* to monitor its progress and verify when it finishes.

---

## Step 2: Code Review - Understanding MCP Tools and AI Agents with Azure Functions

As *azd provision* sets up your cloud resources in the background, you'll explore how **Azure Functions** power AI-enabled tools and agent orchestration.

### What You'll Learn

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

### 2.1 Review: Tool Schema Definition

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
   > - `ToolPropertyList` is a helper class that creates a list of tool properties
   > - Each `ToolProperty` defines a parameter with: name, type, and description
   > - The descriptions are detailed natural language that helps AI agents understand what each parameter is for
   > - Call `.to_json()` to serialize this schema for the MCP protocol

---

### 2.2 Review: MCP Tool Trigger Binding

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
   > - The `@app.mcp_tool_trigger` decorator registers this function as an MCP tool
   > - `arg_name="context"` - the parameter that receives MCP data as a JSON string
   > - `tool_name="save_snippet"` - how AI assistants will refer to this tool
   > - `description` - explains to the AI what this tool does
   > - `tool_properties` - the schema (from section 2.1) serialized as JSON
   > - When deployed, Azure Functions automatically exposes an MCP endpoint that AI assistants can discover

---

### 2.3 Review: Embeddings Input Binding

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
   > - This binding automatically calls Azure OpenAI **before** your function runs
   > - It extracts text from the input and generates vector embeddings
   > - Notice the path difference:
   >   - HTTP: `{code}` references the JSON request body field
   >   - MCP: `{arguments.snippet}` references the MCP context structure
   > - The resulting embedding is passed to your function as the `embeddings` parameter
   > - Inside the function, you parse the JSON string to extract the vector array

---

### 2.4 Review: Durable AI Agents with Microsoft Agent Framework

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

### 2.5 Review: Vector Search Tool

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

---

## Step 3: Local Setup and Installing Python Dependencies

Let's install the Python packages required by the Function App:

1. Ensure your VS Code terminal is in the **src** directory of the cloned repository:

   ```bash
   cd src
   ```

2. Create a Python virtual environment using *uv* (this is faster than *venv*):

   **All platforms:**

   ```bash
   uv venv .venv
   ```

3. Activate the virtual environment:

   **macOS/Linux:**

   ```bash
   source .venv/bin/activate
   ```

   **Windows:**

   ```powershell
   .venv\Scripts\activate
   ```

   *(Your terminal prompt should now be prefixed with **(.venv)**)*

4. Install the required Python packages:

   **All platforms:**

   ```bash
   uv pip install -r requirements.txt
   ```

> **Note**: We'll start the Functions host after verifying that all required settings are available from the provisioning process.

---

## Step 4: Verify Local Settings After Provisioning

1. Check the terminal window where you ran *azd provision* in Step 1. Wait for it to complete successfully.

2. Once provisioning completes, the *postProvision* hook defined in *azure.yaml* automatically runs either *./scripts/generate-settings.ps1* (on Windows) or *./scripts/generate-settings.sh* (on Linux/macOS).

   These scripts generate the necessary settings in your *src/local.settings.json* file.

3. Open your *src/local.settings.json* file in VS Code and verify it now contains populated values.

4. Your *src/local.settings.json* file should now look similar to this (with your specific resource details, and additional keys):

   ![Local Settings](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-LocalSettings.png)

5. **Only needed if settings are missing**

   If for any reason the *local.settings.json* file wasn't properly generated or is missing values, you can manually run the generation script from the repository root:

   ```bash
   # Navigate to repository root if not already there
   cd ..
   ./scripts/generate-settings.sh
   ```

6. Save the file if you made any changes.

---

## Step 5: Start Docker Compose for Durable Task Support

The agent-framework-azurefunctions library leverages the Durable Task emulator to manage agent state locally. Start it using Docker Compose:

1. Ensure you're in the repository root directory:

   ```bash
   # Navigate to repository root if currently in src/
   cd ..
   ```

2. Start the Docker Compose services in detached mode:

   **All platforms:**

   ```bash
   docker compose up -d
   ```

   If prompted to allow network access, select **Allow** to continue.

   This starts the Durable Task emulator container which the agents will use for state persistence.

3. Verify the container is running:

   **All platforms:**

   ```bash
   docker compose ps
   ```

   You should see the durable task emulator service running as well as azurite.

> **Note**: The Durable Task emulator provides local state management for AI agents. In production, this would be handled by the Durable Task Scheduler service.

---

## Step 6: Run Functions Locally and Test with Cloud Resources

Now that *local.settings.json* points to your actual Azure resources provisioned by azd and the Durable Task emulator is running, we can start the Function App and perform end-to-end testing.

1. **Authenticate with Azure:**

   For access to Azure resources, you'll need to perform an az login:

   **All platforms:**

   ```bash
   az login
   ```

   Follow the authentication prompts in your browser. After successful login, if you have multiple subscriptions, select the appropriate one from the terminal.

2. In the same terminal where you activated the virtual environment in Step 3, ensure you're in the **src** directory:

   ```bash
   cd src
   ```

   Your terminal prompt should still show **(.venv)** indicating the virtual environment is active.

3. Start the Azure Functions runtime locally (ensure your *venv* from Step 3 is still activated):

   **All platforms:**

   ```bash
   func start
   ```

   > **Note**: This may take a minute to start.

4. Look for output indicating the Functions host has started successfully. You should see your functions listed, including the HTTP endpoints, the MCP tool trigger functions, and even an orchestration (we'll run this soon), as shown below:

   ![Function Start](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-FuncStart.png)

### 6.1 Test with REST Client (End-to-End Smoke Test) - Optional

Let's test your implementation using the built-in REST Client:

1. In VS Code Explorer, open **src/tests/test.http**. This file contains pre-defined HTTP requests for testing different Snippy endpoints.

2. Find the request block labeled **### Save a new snippet with projectId**. Select the small "Send Request" link directly above the *POST* line.

   ![Http Request](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-HttpSendRequest.png)

3. Check the response panel that appears on the right. You should see a **Status 200 OK** response with JSON data showing the saved snippet details, confirming that:
   - Your function successfully processed the request
   - Azure OpenAI generated embeddings for the code
   - The snippet was stored in Cosmos DB with its vector embedding

4. Now test retrieval: Find the **### Get a snippet by name** request block. Modify the snippet name in the URL (**/api/snippets/{name}**) to match the one you just saved (the default is "test-snippet"). Send this request and verify it returns the correct code snippet data.

5. Test a few more operations to ensure everything works:
   - Save a more complex snippet using the **### Save a complex snippet** request
   - Retrieve it using the corresponding GET request
   - Try the AI agent functions by running the **### Generate wiki** or **### Generate code style guide** requests

6. For the agent-based functions (wiki and code style guide), note that these may take longer to execute (10-30 seconds) as they involve creating an AI agent that analyzes your saved snippets.

These successful tests confirm that your entire pipeline is working: HTTP endpoints, embedding generation, Cosmos DB vector storage, and AI agent integration.

---

## Step 7: Explore MCP Tools in GitHub Copilot (Local Endpoint)

Now, connect GitHub Copilot Chat to your *locally running* Function App's MCP endpoint to test the tools you implemented.

1. **Verify MCP Server Configuration**:
   - In VS Code, open the **.vscode/mcp.json** file
   - You should see the **local-snippy** server already configured
   - If you see a "Running" status with tools count (e.g., "✓ Running | Stop | Restart | 5 tools"), the server is already connected
   - If not connected, select the **Start** button in the file (appears at the top of the JSON configuration)

     ![MCP Local Start](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-MCP-Local-Start.png)

2. **View MCP Server Logs** (optional but helpful):
   - Open the Command Palette by selecting **Ctrl+Shift+P** (Windows/Linux) or **Cmd+Shift+P** (macOS) or **View > Command Palette** from the toolbar
   - Enter and select `MCP: List Servers`
   - Select the **local-snippy** server from the dropdown
   - Select **Show Output** to see the server logs
   - **Tip**: Select the settings icon next to "MCP: local-snippy" in the output panel to change log level to "trace" for more detailed logs

3. **Open GitHub Copilot Chat**:
   - Select **Ctrl+Alt+I** (Windows/Linux) or **Cmd+Alt+I** (macOS) or select the Copilot Chat icon in the Activity Bar

4. **Configure Copilot Chat for Tools**:
   - Ensure **Agent mode** is active (select from the dropdown next to the model selector, or *Ctrl+.* / *Cmd+.*)

     ![Agent Mode](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-AgentMode.png)

   - At the bottom of the chat panel, select the **Tools** icon

     ![Select Tools](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-GH-SelectTools.png)

   - Make sure *MCP Server: local-snippy* and all its tools are checked

   ![MCP Tools Local](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-MCP-Tools-Local.png)

   - Select **Escape** or select **OK** to confirm your selection

> **Troubleshooting MCP Server Connection Issues**
>
> If you're unable to connect to MCP servers, you may be encountering one of these issues:
>
> **Issue 1: Cache-related problems**
>
> To resolve cache issues:
> 1. Open VS Code command palette (**Ctrl+Shift+P** or **Cmd+Shift+P**).
> 2. Enter `MCP Tools: Reset Cached Tools` to execute the command.
>
> **Issue 2: Organization policy restrictions**
>
> If your GitHub Enterprise organization has disabled MCP servers via policies, you have two options:
>
> **Option A: Use a different GitHub account** that isn't subject to the same restrictions
>
> **Option B: Use the MCP Inspector tool**
> 1. Run the inspector locally: `npx @modelcontextprotocol/inspector`.
> 2. Open your browser and navigate to `http://localhost:6274`.
> 3. Test your MCP tools from this local interface.
>
> These workarounds will let you complete the tutorial exercises even if organizational policies restrict direct MCP server access.

5. **Test the *save_snippet* Tool**:
   - Open any code file (e.g., **src/durable_agents.py**)
   - Select some interesting code sections (or it'll take the entire file as a snippet, which is fine, as well)
   - In Copilot Chat, enter:

     ```
     #local-snippy save this snippet as ai-agents-service-usage
     ```

     Press **Enter** or **Send**
   - If prompted by Copilot to use the **save_snippet** tool, select **Allow**

     ![Save Snippet Local](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-SaveSnippet-Local.png)

6. **Test the *get_snippet* Tool**:
   - In Copilot Chat, enter:

     ```
     #local-snippy get the snippet named ai-agents-service-usage
     ```

     Press **Enter** or **Send**
   - Copilot will suggest using the **get_snippet** tool - Select **Allow**

     ![Get Snippet Local](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-GetSnippet-Local.png)

7. **Experiment with Advanced AI Agent Tools**:
   - Try these prompts (no need to select code first):
     - `generate a deep wiki for all snippets and place in a new file deep-wiki.md in project root`
       (uses the *deep_wiki* tool)

     - `create a code style guide based on the saved snippets and place in a new file code-style.md in project root`
       (uses the *code_style* tool)

   > **Note**: These agent-based tools may take a minute to run as they orchestrate with configured tools and have self-reflection

   - Once they are done, open the files and Preview the generated Markdown (*Ctrl+K V* or *Cmd+K V*)

8. **Check Function Logs**:
   - In the terminal where `func start` is running, you'll see logs for each tool invocation
   - This confirms your MCP tools are working end-to-end

The ability to interact with your tools through natural language in Copilot demonstrates the power of the MCP protocol - AI assistants can seamlessly discover and use your Azure Functions without any custom integration code.

---

## Step 8: Test Multi-Agent Orchestration with Durable Task Scheduler

Now you'll test the `generate_comprehensive_documentation` tool, which orchestrates multiple AI agents working together in sequence. This demonstrates how the Durable Task Scheduler manages complex, stateful workflows.

1. **Open the Durable Task Scheduler UI**:
   - In your browser, navigate to `http://localhost:8082/`
   - This is the Durable Task Scheduler's web interface running in the Docker container
   - You'll see the orchestration dashboard where you can monitor workflows in real-time

2. **Trigger the Multi-Agent Orchestration**:
   - In GitHub Copilot Chat (with the **local-snippy** MCP server active), enter the following prompt:

     ```
     #local-snippy Generate comprehensive documentation with emphasis on the MCP tools, vector search capabilities and code style. Save in a new file called comprehensive-documentation.md
     ```

   - Select **Allow** when Copilot asks to use the **generate_comprehensive_documentation** tool

3. **Monitor the Orchestration**:
   - Switch to your browser at `http://localhost:8082/`
   - You should see a new orchestration instance appear in the dashboard
   - Watch as the orchestration progresses through multiple stages:
     - **DeepWiki Agent** generates initial documentation
     - **DeepWiki Agent** refines the documentation with additional details
     - **CodeStyle Agent** generates a complementary style guide
   - Each step shows the agent calls, tool invocations, and intermediate results

4. **Check the Function Logs**:
   - In the terminal where `func start` is running, observe the detailed logs showing:
     - Orchestration startup
     - Agent invocations (DeepWikiAgent, CodeStyleAgent)
     - Vector search tool calls
     - State persistence operations

5. **Review the Generated Documentation**:
   - Once the orchestration completes (this may take 1-2 minutes), check your workspace
   - Open **comprehensive-documentation.md** in the project root
   - The file should contain:
     - Comprehensive wiki-style documentation generated by DeepWikiAgent
     - Code style guide generated by CodeStyleAgent
     - All focused on MCP tools and vector search capabilities as requested

6. **Review the Completed Orchestration in the Dashboard**:
   - Return to the Durable Task Scheduler UI at `http://localhost:8082/`
   - Find your completed orchestration instance in the list (it should show **Completed** status)
   - Click on the orchestration to view its detailed execution history:
     - **Timeline view**: See the sequence of all agent calls and their durations
     - **Agent outputs**: Review the intermediate results from each agent (DeepWiki and CodeStyle)
     - **Tool invocations**: Examine which vector searches were performed and what snippets were retrieved
     - **State transitions**: Understand how the orchestration moved through each stage
   - This detailed view helps you understand how Durable Functions orchestrated the multi-agent workflow and managed state persistence throughout the entire process
   - Notice how each agent call is tracked as a separate activity, allowing you to debug and optimize complex workflows

> **What Just Happened:**
>
> You triggered a complex multi-agent workflow that:
> 1. Used an MCP tool (`generate_comprehensive_documentation`) to start a Durable Functions orchestration
> 2. The orchestration coordinated two AI agents (DeepWiki and CodeStyle) in sequence
> 3. Each agent used the `vector_search` tool to find relevant code snippets
> 4. The Durable Task Scheduler managed the entire workflow, persisting state between each step
> 5. Results were combined and saved to a file via Copilot
>
> This demonstrates the power of combining:
> - **MCP protocol** for AI assistant integration
> - **Durable Functions** for workflow orchestration
> - **AI Agents** for specialized tasks
> - **Durable Task Scheduler** for local state management

---

## Step 9: Deploy the Application Code to Azure

You've implemented the code and verified it works locally against your provisioned cloud resources. Now, deploy the application code to the Azure Function App created by *azd provision*.

1. Go back to the Terminal and stop the local Functions host (View → Terminal)

   If it's still running - **Ctrl+C** (or **Cmd+C** on macOS) in the *func start* terminal - wait a few seconds.

2. Ensure your terminal is in the repository root directory (the one containing *azure.yaml*):

   ```bash
   # Navigate to repository root
   cd ..
   ```

3. Run the AZD deploy command:

   **All platforms:**

   ```bash
   azd deploy
   ```

   > **Note**: This may take a couple minutes to deploy.

   This command performs the following:
   - Reads the *azure.yaml* file to determine which service code to deploy (configured to deploy the *src* directory to the Function App)
   - Packages your application code
   - Deploys the code to the Azure Function App provisioned earlier
   - Configures the application settings in the deployed Function App based on your *.azure/snippy-mcp-lab-<unique-suffix>/.env* file, ensuring it can connect to OpenAI, Cosmos DB, etc., in the cloud

4. Wait for the deployment to complete successfully. AZD will output the endpoints for your deployed application, including the Function App's base URL (e.g., *https://func-api-...azurewebsites.net*).

---

## Step 10: Connect VS Code / Copilot to the Cloud MCP Endpoint

Finally, configure VS Code and Copilot Chat to use the tools running on your *deployed* Azure Function App.

1. **Get the MCP System Key:**

   The cloud MCP endpoint (**/runtime/webhooks/mcp**) is protected by a system key. You'll need this key to authenticate calls. Run the following commands in your VS Code terminal to retrieve the system key:

   **macOS/Linux:**

   ```bash
   appName=$(azd env get-value AZURE_FUNCTION_NAME)
   az functionapp keys list -n $appName --query "systemKeys.mcp_extension" -g rg-snippymcplab-<unique-suffix> --output tsv
   ```

   **Windows:**

   ```powershell
   $appName = azd env get-value AZURE_FUNCTION_NAME
   az functionapp keys list -n $appName --query "systemKeys.mcp_extension" -g rg-snippymcplab-<unique-suffix> --output tsv
   ```

   > **Note**: Replace `<unique-suffix>` with the suffix you chose in Step 1.3.

   The output will be a long string - **copy this value**. This is your **system-key** required for calling the MCP endpoint.

2. **Add Cloud Endpoint to *.vscode/mcp.json*:**

   After retrieving your Function App name and MCP system key, you can now configure the cloud endpoint in *.vscode/mcp.json*.

   Stop the **local-snippy** server if it is still running.

   Select **Start** above **remote-snippy** in *mcp.json* - this will prompt you to enter:
   - The Function App name
   - The MCP system key

   You don't need to manually replace any values in the JSON - just copy the following values from your Terminal:

   **macOS/Linux:**

   ```bash
   # Print the Function App name
   echo $appName
   ```

   **Windows:**

   ```powershell
   # Print the Function App name
   $appName
   ```

   Use the *$appName* value for the *functionapp-name* input, and paste the system key you retrieved earlier.

   This setup allows the cloud-hosted MCP to receive and stream events securely.

   ![MCP Remote](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-MCP-Remote.png)

3. **Switch Copilot to Cloud Server:**

   - Open Copilot Chat (**Ctrl+Alt+I** or **Cmd+Alt+I**)
   - Ensure **Agent** mode is selected
   - Verify the tools are loaded correctly

4. **Test Cloud hosted Tools:**

   Repeat the tests from earlier, but this time with the *remote-snippy* server:

   - Select some code
   - Ask Copilot:

     ```
     #remote-snippy save the selected snippet as my-cloud-mcp-test
     ```

   - Confirm the tool usage
   - Ask Copilot:

     ```
     #remote-snippy get the snippet named my-cloud-mcp-test
     ```

   - Try other tools like **deep_wiki** as we did earlier

   Verify that the tools work correctly by interacting with your deployed Azure Function App.

---

## Step 11: Monitor Cloud Orchestration with DTS Dashboard

Now that the application is deployed to Azure, you can monitor the multi-agent orchestration running in the cloud using the Durable Task Scheduler (DTS) dashboard.

1. **Generate the DTS Dashboard URL:**

   The repository includes helper scripts to generate the DTS dashboard URL. In your VS Code terminal (ensure you're in the repository root directory), run:

   ```bash
   ./scripts/get-dts-dashboard-url.sh
   ```

   The script will output a URL similar to:

   ```text
   https://dashboard.durabletask.io/subscriptions/{subscription-id}/schedulers/{dts-name}/taskhubs/{taskhub-name}?endpoint={encoded-endpoint}&tenantId={tenant-id}
   ```

2. **Copy and open the dashboard URL:**

   - Copy the entire URL from the terminal output
   - Open it in your browser (you may need to sign in with your Azure credentials)
   - You should see the Durable Task Scheduler dashboard for your deployed application

3. **Trigger a Cloud Orchestration:**

   Back in VS Code, open GitHub Copilot Chat and run the multi-agent orchestration against your deployed function. Use this exact prompt to ensure it calls the comprehensive documentation tool:

   ```
   #remote-snippy use the generate_comprehensive_documentation tool to create documentation and save it in a new file called cloud-documentation.md
   ```

   - Select **Allow** when Copilot asks to use the **generate_comprehensive_documentation** tool
   - This time the orchestration will run on the Azure Durable Task Scheduler service in the cloud

4. **Monitor the Orchestration in the Dashboard:**

   - Switch to the browser tab with the DTS dashboard
   - You should see a new orchestration instance appear
   - Watch as it progresses through the same stages you saw locally:
     - **DeepWikiAgent** initial documentation generation
     - **DeepWikiAgent** refinement pass
     - **CodeStyleAgent** style guide generation
   - Select the orchestration instance to view detailed execution history:
     - Timeline of agent calls and durations
     - Agent outputs and intermediate results
     - Vector search tool invocations
     - State transitions throughout the workflow

5. **Review the Generated Documentation:**

   Once the orchestration completes (1-2 minutes), check your workspace:
   - Open **cloud-documentation.md** in the project root
   - Compare it with the **comprehensive-documentation.md** generated during local testing
   - Both files demonstrate the same multi-agent workflow, but one ran locally and one in Azure

> **What You've Demonstrated:**
>
> You've now run the same multi-agent orchestration in two environments:
>
> - **Local**: Using Docker-based Durable Task emulator for development
> - **Cloud**: Using Azure Durable Task Scheduler for production
>
> The DTS dashboard provides:
>
> - Real-time monitoring of orchestration progress
> - Detailed execution history and debugging information
> - Visibility into agent calls, tool invocations, and state management
> - The ability to track and troubleshoot complex multi-agent workflows
>
> This demonstrates how Durable Functions provides a consistent development experience from local to cloud, with enterprise-grade observability for AI agent orchestrations.

---

## Step 12: Clean Up Azure Resources

When you are finished with the tutorial, delete the Azure resources created by *azd provision*.

1. Open a terminal in VS Code

2. Ensure you are in the repository root directory:

   ```bash
   # Navigate to repository root if needed
   cd ..
   ```

3. Run the following AZD command:

   **All platforms:**

   ```bash
   azd down --purge --force
   ```

   - `--purge` attempts to permanently delete resources like Key Vaults that support soft-delete
   - `--force` skips the confirmation prompt

4. AZD will list the resources being deleted and remove them from Azure. This will also delete the local AZD environment configuration (**.azure** folder).

   > **Note**: This may take around 20 minutes to complete.

---

## Conclusion

Congratulations on completing the Snippy tutorial! You've successfully built a powerful, AI-enhanced code snippet manager that demonstrates cutting-edge integration patterns between serverless compute and AI services. Let's recap what you've learned and accomplished:

## Key Technologies and Concepts Mastered

### 1. Azure Functions as an AI Integration Platform

You've built a complete serverless application using Azure Functions that serves both as a traditional API and as an MCP tool provider for AI assistants. This demonstrates how Azure Functions provides an ideal foundation for AI-powered applications, offering serverless scalability with minimal infrastructure overhead.

### 2. Model Context Protocol (MCP) Integration

You've implemented and deployed MCP tools that enable AI assistants like GitHub Copilot to discover and use your Azure Functions via a standardized protocol. This powerful capability allows any MCP-compatible AI assistant to leverage your tools without custom integration code - they simply connect to the `/runtime/webhooks/mcp` endpoint and discover available tools automatically.

### 3. Vector Embeddings and Semantic Search

You've explored a complete Retrieval-Augmented Generation (RAG) pattern by:
- Using Azure OpenAI's embedding models to convert code snippets into vector representations
- Leveraging Azure Functions' `@app.embeddings_input` binding to automatically generate embeddings before your function executes
- Storing these vectors in Cosmos DB's DiskANN vector index for high-performance similarity search
- Implementing the `vector_search` tool that AI agents use to find relevant code snippets semantically

### 4. AI Agent Framework Integration

You've explored how Microsoft Agent Framework enables sophisticated AI agent capabilities:
- Using `ChatAgent` from agent-framework to create specialized agents (DeepWiki and CodeStyle)
- Integrating `AzureOpenAIChatClient` to leverage Azure OpenAI's Chat Completions API
- Providing agents with custom tools like `vector_search` for enhanced capabilities
- Managing multi-agent orchestrations with Durable Functions that coordinate sequential agent calls
- Leveraging Durable Entities for automatic state persistence and conversation history

### 5. Durable Functions Orchestration

You've learned how Durable Functions orchestrates complex, stateful workflows:
- Creating orchestrations that coordinate multiple AI agents in sequence
- Using `app.get_agent()` to access agent wrappers within orchestrations
- Managing conversation threads across multiple agent calls to maintain context
- Monitoring orchestration state and progress through the Durable Task Scheduler dashboard

### 6. Dual-Interface Architecture

You've explored a system that exposes functionality through multiple interfaces:
- Traditional HTTP endpoints (`@app.route`) for standard RESTful API access
- MCP tools (`@app.mcp_tool_trigger`) for AI assistant integration
- Auto-generated agent endpoints (`/api/agents/{AgentName}/run`) via AgentFunctionApp
- Orchestration endpoints for triggering complex multi-agent workflows

### 7. DevOps with Azure Developer CLI

You've used Azure Developer CLI (azd) to automate the provisioning and deployment of all required resources:
- Azure Function App with Flex Consumption Plan for cost-effective serverless compute
- Azure Cosmos DB with vector search capability using DiskANN indexing
- Azure OpenAI with embeddings (text-embedding-3-small) and chat models deployed
- Automated configuration management with post-provision scripts generating local.settings.json

---

## Technical Implementation Highlights

1. **MCP Tool Registration**: You implemented the `@app.mcp_tool_trigger` decorator with `ToolPropertyList` schema definitions to register Azure Functions as discoverable MCP tools (save_snippet, get_snippet, deep_wiki, code_style, generate_comprehensive_documentation).

2. **Automated Vector Embedding**: You leveraged the `@app.embeddings_input` binding with path expressions like `{code}` and `{arguments.snippet}` to automatically generate embeddings before your function executes, eliminating manual Azure OpenAI client code.

3. **Vector Database Configuration**: You explored how Cosmos DB is configured with DiskANN vector search using the `VectorEmbedding` container policy, enabling fast semantic retrieval with cosine distance similarity.

4. **Microsoft Agent Framework Integration**: You examined how `ChatAgent` instances are created with `AzureOpenAIChatClient`, configured with system prompts and custom tools, and wrapped by `AgentFunctionApp` for Durable Functions integration with automatic state management.

5. **Multi-Agent Orchestration**: You implemented the `documentation_orchestration` function that demonstrates how to coordinate multiple agents (DeepWiki and CodeStyle) in sequence using Durable Functions, sharing context through conversation threads.

6. **End-to-End Testing**: You tested your implementation through multiple interfaces:
   - HTTP requests using REST Client extension
   - Local MCP endpoint via GitHub Copilot connected to `http://localhost:7071`
   - Cloud MCP endpoint via GitHub Copilot connected to deployed Azure Function App
   - Durable Task Scheduler dashboard for monitoring orchestrations

---

## Practical Applications and Next Steps

The patterns and technologies you've learned in this tutorial have broad applications:

- **Enhanced Developer Experiences**: Create custom MCP tools that extend AI coding assistants with domain-specific knowledge, company APIs, and proprietary workflows
- **Knowledge Management Systems**: Build semantic search systems that capture, index, and retrieve organizational knowledge using vector embeddings and RAG patterns
- **AI-Powered Automation**: Create specialized AI agents that execute complex workflows using serverless functions as tools, with built-in state management and resilience
- **Multi-Agent Systems**: Orchestrate teams of AI agents with different specializations working together on complex tasks
- **Hybrid AI Architectures**: Combine the reasoning capabilities of LLMs with the precision and reliability of traditional serverless functions

---

## Additional Resources

- [Azure Functions documentation](https://learn.microsoft.com/azure/azure-functions/)
- [Model Context Protocol specification](https://modelcontextprotocol.io/)
- [Azure OpenAI Service documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Cosmos DB vector search documentation](https://learn.microsoft.com/azure/cosmos-db/vector-search)
- [Microsoft Agent Framework documentation](https://github.com/microsoft/agent-framework)
- [Durable Functions documentation](https://learn.microsoft.com/azure/azure-functions/durable/)

---

Thank you for completing this tutorial!
