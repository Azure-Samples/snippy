# Snippy Lab - Build an AI-Powered Code Snippet Manager

Welcome! This hands-on lab teaches you to build **Snippy**, an intelligent code snippet manager using Azure Functions, Azure OpenAI, and the Model Context Protocol (MCP).

## What You'll Build

- **Serverless API** with Azure Functions for saving/retrieving code snippets
- **Vector Search** using Azure OpenAI embeddings and Cosmos DB
- **MCP Tools** that GitHub Copilot can discover and use
- **AI Agents** that generate documentation and style guides from your code
- **Multi-Agent Orchestration** using Durable Functions

![Snippy Architecture](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/Snippy-Architecture-V2.png)

## Prerequisites

Before starting, ensure you have:

### Required Software
- **Visual Studio Code** - [Download](https://code.visualstudio.com/)
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Git** - [Download](https://git-scm.com/)
- **Azure CLI** - [Install](https://docs.microsoft.com/cli/azure/install-azure-cli)
- **Azure Functions Core Tools v4** - [Install](https://docs.microsoft.com/azure/azure-functions/functions-run-local)
- **Azure Developer CLI (azd)** - [Install](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)

### Recommended
- **uv** package manager (faster than pip) - [Install](https://github.com/astral-sh/uv)

### Required Accounts
- **Azure Subscription** - [Create free account](https://azure.microsoft.com/free/)
- **GitHub Account with Copilot** - [GitHub Copilot](https://github.com/features/copilot)

## Quick Start

1. **Clone this repository**
   ```bash
   git clone https://github.com/Azure-Samples/snippy.git
   cd snippy
   ```

2. **Follow the tutorial**
   - Open [TUTORIAL.md](./TUTORIAL.md) for step-by-step instructions
   - Refer to [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if you encounter issues

3. **Clean up when done**
   ```bash
   azd down --purge --force
   ```

## What You'll Learn

- **Azure Functions** as an AI integration platform
- **Model Context Protocol (MCP)** for AI assistant integration
- **Vector embeddings** and semantic search with RAG patterns
- **Microsoft Agent Framework** for building AI agents
- **Durable Functions** for multi-agent orchestration
- **Azure OpenAI** integration with embeddings and chat models

## Support

- **Issues**: Found a bug? [Open an issue](https://github.com/Azure-Samples/snippy/issues)
- **Questions**: Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) first
- **Discussions**: [GitHub Discussions](https://github.com/Azure-Samples/snippy/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE.md](../LICENSE.md) file for details.
