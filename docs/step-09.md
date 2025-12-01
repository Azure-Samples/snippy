# Step 9: Deploy the Application Code to Azure

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
