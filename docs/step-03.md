# Step 3: Local Setup and Installing Python Dependencies

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
