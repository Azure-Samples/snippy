# Step 5: Start Docker Compose for Durable Task Support

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
