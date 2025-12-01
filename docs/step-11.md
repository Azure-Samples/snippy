# Step 11: Monitor Cloud Orchestration with DTS Dashboard

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
