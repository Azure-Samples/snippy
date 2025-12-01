# Step 4: Verify Local Settings After Provisioning

1. Check the terminal window where you ran *azd provision* in Step 1. Wait for it to complete successfully.

2. Once provisioning completes, the *postProvision* hook defined in *azure.yaml* automatically runs either *./scripts/generate-settings.ps1* (on Windows) or *./scripts/generate-settings.sh* (on Linux/macOS).

   These scripts generate the necessary settings in your *src/local.settings.json* file.

3. Open your *src/local.settings.json* file in VS Code and verify it now contains populated values.

4. Your *src/local.settings.json* file should now look similar to this (with your specific resource details, and additional keys):

    ![Local Settings](https://raw.githubusercontent.com/Azure-Samples/snippy/main/images/SnippyLab-LocalSettings.png)

5. **Only needed if settings are missing**

    If for any reason the *local.settings.json* file wasn't properly generated or is missing values, you can manually run the generation script from the repository root:

    ```bash
    # Navigate to repository root if not already there
    cd ..
    ./scripts/generate-settings.sh
    ```

6. Save the file if you made any changes.
