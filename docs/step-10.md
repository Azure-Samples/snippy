# Step 10: Connect VS Code / Copilot to the Cloud MCP Endpoint

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
