# Quick Reference

Essential commands and tips for working with Snippy.

## Setup Commands

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/Azure-Samples/snippy.git
cd snippy

# Login to Azure
az login

# Login to Azure Developer CLI
azd auth login
```

### Create Environment

```bash
# Create a unique azd environment
azd env new snippymcplab-<unique-suffix> --subscription <your-subscription-id>

# Set name suffix
azd env set NAME_SUFFIX <unique-suffix>

# Provision Azure resources (takes 5-10 minutes)
azd provision
```

### Python Setup

```bash
# Navigate to src directory
cd src

# Create virtual environment with uv
uv venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows PowerShell
.venv\Scripts\activate.bat  # Windows CMD

# Install dependencies
uv pip install -r requirements.txt
```

### Start Local Development

```bash
# Start Docker services (from root directory)
docker compose up -d

# Start Functions host (from src directory)
cd src
func start
```

## Common Tasks

### Regenerate Settings

```bash
# From repository root
./scripts/generate-settings.sh  # macOS/Linux
.\scripts\generate-settings.ps1  # Windows
```

### Deploy to Azure

```bash
# From repository root
azd deploy
```

### Get Function App Details

```bash
# Get function app name
azd env get-value AZURE_FUNCTION_NAME

# Get resource group
azd env get-value AZURE_RESOURCE_GROUP

# Get MCP system key
az functionapp keys list \
  -n $(azd env get-value AZURE_FUNCTION_NAME) \
  -g $(azd env get-value AZURE_RESOURCE_GROUP) \
  --query "systemKeys.mcp_extension" \
  --output tsv
```

### View Logs

```bash
# Local function logs
# (visible in terminal where `func start` is running)

# Docker container logs
docker compose logs

# Azure function logs
func azure functionapp logstream <function-app-name>
```

## MCP Configuration

### Local MCP Server

In `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "local-snippy": {
      "type": "sse",
      "url": "http://localhost:7071/runtime/webhooks/mcp"
    }
  }
}
```

### Remote MCP Server

After deployment, update `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "remote-snippy": {
      "type": "sse",
      "url": "https://<function-app-name>.azurewebsites.net/runtime/webhooks/mcp",
      "headers": {
        "x-functions-key": "<mcp-system-key>"
      }
    }
  }
}
```

## Copilot Commands

### Using MCP Tools

``` text
# Save a snippet
#local-snippy save this snippet as my-snippet-name

# Retrieve a snippet
#local-snippy get the snippet named my-snippet-name

# Generate documentation
#local-snippy generate a deep wiki for all snippets

# Create style guide
#local-snippy create a code style guide based on saved snippets

# Multi-agent orchestration
#local-snippy generate comprehensive documentation
```

## Testing Endpoints

### Using VS Code REST Client

Open `src/tests/test.http` and click "Send Request" above any request.

### Using curl

```bash
# Save a snippet
curl -X POST http://localhost:7071/api/snippets \
  -H "Content-Type: application/json" \
  -d '{"name":"test","code":"print(\"hello\")","projectId":"default"}'

# Get a snippet
curl http://localhost:7071/api/snippets/test
```

## Troubleshooting Quick Fixes

### Port Already in Use

```bash
# Kill process on port 7071
lsof -ti:7071 | xargs kill -9  # macOS/Linux
Get-Process -Id (Get-NetTCPConnection -LocalPort 7071).OwningProcess | Stop-Process  # Windows
```

### Docker Not Running

```bash
# Check Docker status
docker ps

# Restart Docker Desktop app if needed
```

### Virtual Environment Issues

```bash
# Deactivate and recreate
deactivate
rm -rf .venv
uv venv .venv
source .venv/bin/activate  # or Windows equivalent
uv pip install -r requirements.txt
```

### MCP Not Connecting

1. Command Palette → `MCP Tools: Reset Cached Tools`
2. Restart VS Code
3. Check `.vscode/mcp.json` configuration
4. View logs: Command Palette → `MCP: List Servers` → Show Output

## Cleanup

### Full Cleanup

```bash
# Delete all Azure resources
azd down --purge --force

# Stop Docker containers
docker compose down -v

# Remove local config
rm -rf .azure
```

### Verify Cleanup

```bash
# Check resource group is deleted
az group list --output table

# Check Docker containers stopped
docker ps
```

## Useful Links

- **Azure Portal**: https://portal.azure.com
- **Microsoft Foundry**: https://ai.azure.com
- **MCP Inspector**: `npx @modelcontextprotocol/inspector`
- **DTS Dashboard** (local): http://localhost:8082
- **Azurite Blob Storage** (local): http://127.0.0.1:10000

## File Locations

- **Function code**: `src/function_app.py`
- **Agent code**: `src/durable_agents.py`
- **Tools**: `src/tools/vector_search.py`
- **Settings**: `src/local.settings.json`
- **MCP config**: `.vscode/mcp.json`
- **Docker config**: `docker-compose.yml`
- **Infrastructure**: `infra/main.bicep`

## Next Steps

1. **Complete the tutorial**: See [TUTORIAL.md](./TUTORIAL.md)
2. **Having issues?**: Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
