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

## Tutorial Steps

Follow these steps in order to complete the tutorial:

1. [**Set Up Azure Resources**](step-01.md) - Provision Azure infrastructure with Azure Developer CLI
2. [**Code Review - Understanding MCP Tools and AI Agents**](step-02.md) - Explore the implementation patterns
3. [**Local Setup and Installing Python Dependencies**](step-03.md) - Set up your development environment
4. [**Verify Local Settings After Provisioning**](step-04.md) - Confirm configuration is correct
5. [**Start Docker Compose for Durable Task Support**](step-05.md) - Run local services for agent state management
6. [**Run Functions Locally and Test with Cloud Resources**](step-06.md) - Test the application end-to-end
7. [**Explore MCP Tools in GitHub Copilot (Local Endpoint)**](step-07.md) - Connect Copilot to your local functions
8. [**Test Multi-Agent Orchestration with Durable Task Scheduler**](step-08.md) - Run complex AI workflows
9. [**Deploy the Application Code to Azure**](step-09.md) - Push your code to the cloud
10. [**Connect VS Code / Copilot to the Cloud MCP Endpoint**](step-10.md) - Use deployed functions from Copilot
11. [**Monitor Cloud Orchestration with DTS Dashboard**](step-11.md) - Observe production workflows
12. [**Clean Up Azure Resources**](step-12.md) - Remove resources to avoid charges

---

## What You'll Build

By the end of this tutorial, you will have:

- **Serverless API** with Azure Functions for saving/retrieving code snippets
- **Vector Search** using Azure OpenAI embeddings and Cosmos DB
- **MCP Tools** that GitHub Copilot can discover and use
- **AI Agents** that generate documentation and style guides from your code
- **Multi-Agent Orchestration** using Durable Functions

## Technologies Used

- **Azure Functions** (Python v2, Blueprint model)
- **Azure OpenAI** (GPT-4o-mini, text-embedding-3-small)
- **Azure Cosmos DB** (with vector search)
- **Model Context Protocol (MCP)**
- **Microsoft Agent Framework**
- **Durable Functions & Durable Task Scheduler**

---

Ready to get started? Head to [**Step 1: Set Up Azure Resources**](step-01.md)!
