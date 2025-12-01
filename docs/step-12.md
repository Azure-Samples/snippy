# Step 12: Clean Up Azure Resources

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
