# Troubleshooting Guide

This guide covers common issues you might encounter while working through the Snippy lab.

## Azure CLI & Authentication

### Issue: `az login` fails or times out

**Solution:**
```bash
# Try device code authentication instead
az login --use-device-code
```

### Issue: "No subscriptions found"

**Solution:**
```bash
# List all available subscriptions
az account list --output table

# Set a specific subscription
az account set --subscription "<subscription-id>"
```

### Issue: Insufficient permissions to create resources

**Solution:**
- Ensure you have **Contributor** or **Owner** role on the subscription
- Contact your Azure administrator if you're using a company subscription

## Azure Developer CLI (azd)

### Issue: `azd provision` fails with region errors

**Solution:**
```bash
# Try a different Azure region
azd env set AZURE_LOCATION eastus

# Or use the region selector script
./scripts/randomize-region.sh  # macOS/Linux
.\scripts\randomize-region.ps1  # Windows PowerShell
```

### Issue: Resource names already taken

**Solution:**
```bash
# Use a different name suffix
azd env set NAME_SUFFIX <new-unique-suffix>

# Example: your initials + date
azd env set NAME_SUFFIX jd1120
```

### Issue: `azd deploy` fails

**Solution:**
```bash
# Verify environment is set up correctly
azd env list

# Re-run deployment
azd deploy

# If still failing, try provisioning and deploying together
azd up
```

## Python & Virtual Environments

### Issue: `uv` command not found

**Solution:**
Use `pip` instead:
```bash
# Create virtual environment
python -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (Windows Command Prompt)
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Issue: Python version mismatch

**Solution:**
```bash
# Check your Python version
python --version

# Must be 3.11 or higher
# If not, install Python 3.11+ and use:
python3.11 -m venv .venv
```

### Issue: Virtual environment won't activate

**Solution (Windows PowerShell):**
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Solution (macOS/Linux):**
```bash
# Ensure script has execute permissions
chmod +x .venv/bin/activate
```

## Azure Functions

### Issue: `func start` fails - Port 7071 already in use

**Solution:**
```bash
# Find and stop the process using port 7071
# macOS/Linux
lsof -ti:7071 | xargs kill -9

# Windows PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 7071).OwningProcess | Stop-Process -Force

# Or use a different port
func start --port 7072
```

### Issue: Functions host won't start - missing settings

**Solution:**
```bash
# Ensure local.settings.json exists
cd src
ls local.settings.json

# If missing, regenerate it
cd ..
./scripts/generate-settings.sh  # macOS/Linux
.\scripts\generate-settings.ps1  # Windows
```

### Issue: "Cannot find module 'azure.functions'"

**Solution:**
```bash
# Ensure virtual environment is activated (you should see (.venv) in prompt)
# Then reinstall dependencies
pip install -r requirements.txt
```

## Docker

### Issue: Docker daemon not running

**Solution:**
- Start Docker Desktop application
- Wait for it to fully start (whale icon in system tray should be steady)
- Retry: `docker compose up -d`

### Issue: `docker compose up` fails with network errors

**Solution:**
```bash
# Stop any existing containers
docker compose down

# Remove networks
docker network prune -f

# Restart
docker compose up -d
```

### Issue: Azurite or DTS emulator not starting

**Solution:**
```bash
# Check container status
docker compose ps

# View logs
docker compose logs

# Restart specific service
docker compose restart azurite
docker compose restart durable-task-emulator
```

## MCP (Model Context Protocol)

### Issue: MCP server not connecting in VS Code

**Solution 1 - Reset cache:**
1. Open Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
2. Run: `MCP Tools: Reset Cached Tools`

**Solution 2 - Check configuration:**
1. Open `.vscode/mcp.json`
2. Verify the configuration is correct
3. Click "Start" button in the file

**Solution 3 - Check logs:**
1. Command Palette → `MCP: List Servers`
2. Select your server
3. Click "Show Output"
4. Look for error messages

### Issue: MCP tools not showing in Copilot

**Solution:**
1. Open Copilot Chat (`Ctrl+Alt+I`)
2. Enable **Agent mode** (dropdown or `Ctrl+.`)
3. Click **Tools** icon at bottom of chat
4. Verify MCP server and tools are checked
5. Click OK

### Issue: Organization policy blocks MCP servers

**Solution - Use MCP Inspector:**
```bash
# Run inspector locally
npx @modelcontextprotocol/inspector

# Open browser to http://localhost:6274
# Connect to your MCP server there
```

## GitHub Copilot

### Issue: Not signed in to GitHub Copilot

**Solution:**
1. Click account icon (bottom-left of VS Code)
2. Select "Sign in to use AI Features"
3. Choose "Continue with GitHub"
4. Authorize VS Code

### Issue: Copilot not using Claude Sonnet 4.5

**Solution:**
1. Open Copilot Chat
2. Click model selector dropdown
3. Select "Claude Sonnet 4.5"

## Cosmos DB

### Issue: Vector search queries returning no results

**Solution:**
1. Verify embeddings were generated (check Function logs)
2. Ensure you saved snippets in the same project
3. Check container has vector policy configured:
   ```bash
   # View Cosmos DB in Azure Portal
   # Navigate to Data Explorer → snippets container → Settings
   # Verify vector embedding policy exists
   ```

## Network & Connectivity

### Issue: Cannot connect to Azure services locally

**Solution:**
```bash
# Ensure you're authenticated
az account show

# If not logged in
az login --use-device-code
```

### Issue: Timeouts when calling Azure OpenAI

**Solution:**
1. Check Azure OpenAI resource is deployed and running (Azure Portal)
2. Verify API key or managed identity has access
3. Check network connectivity to Azure

## Common Error Messages

### "ModuleNotFoundError: No module named 'azure'"

**Solution:** Virtual environment not activated or dependencies not installed
```bash
source .venv/bin/activate  # or Windows equivalent
pip install -r requirements.txt
```

### "ConnectionError: Unable to connect to Cosmos DB"

**Solution:** Check connection string in `local.settings.json` and verify Cosmos DB is provisioned

### "AuthenticationError: OpenAI API"

**Solution:** Verify `AZURE_OPENAI_KEY` or managed identity credentials in `local.settings.json`

## Getting More Help

If you're still stuck:

1. **Check Function Logs** - Most issues show detailed errors in the terminal where `func start` is running
2. **Check Azure Portal** - Verify all resources are created and running
3. **Review Generated Settings** - Open `src/local.settings.json` and verify all values are populated
4. **GitHub Issues** - Search existing issues or create a new one: https://github.com/Azure-Samples/snippy/issues

## Clean Up (If Starting Over)

If you want to start fresh:

```bash
# Delete Azure resources
azd down --purge --force

# Delete local environment
rm -rf .azure

# Delete virtual environment
rm -rf src/.venv

# Stop Docker containers
docker compose down -v

# Start over from Step 1
```
