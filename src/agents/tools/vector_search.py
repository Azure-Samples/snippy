# Module for vector similarity search tool:
# - Generates text embeddings for the query using Azure OpenAI directly
# - Queries Cosmos DB vector index for similar code snippets
# - Returns results as a JSON string
import json
import logging
import os
from azure.identity.aio import DefaultAzureCredential
from openai import AsyncAzureOpenAI
from data import cosmos_ops

# Configure logging for this module
logger = logging.getLogger(__name__)

# Reduce Azure SDK logging
logging.getLogger("azure").setLevel(logging.WARNING)

# Performs vector similarity search on code snippets
# Args:
#     query: The search query text (plain language or code fragment)
#     k: Number of top matches to return
#     project_id: The project ID to scope the search
# Returns:
#     JSON string of matching snippets with their IDs, code, and similarity scores
async def vector_search(query: str, k: int = 30, project_id: str = "default-project") -> str:
    """
    Performs vector similarity search on code snippets.
    
    Args:
        query: The search query text (plain language or code fragment)
        k: Number of top matches to return
        project_id: The project ID to scope the search
        
    Returns:
        JSON string of matching snippets with their IDs, code, and similarity scores
    """
    logger.info("Starting vector search with query: '%s', k: %d, project_id: %s", query, k, project_id)
    
    # Retrieve required environment variables
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    model_deployment_name = os.environ.get("EMBEDDING_MODEL_DEPLOYMENT_NAME")

    # Validate configuration
    if not azure_openai_endpoint or not model_deployment_name:
        logger.error("Missing required environment variables. AZURE_OPENAI_ENDPOINT: %s, EMBEDDING_MODEL_DEPLOYMENT_NAME: %s",
                    "present" if azure_openai_endpoint else "missing",
                    "present" if model_deployment_name else "missing")
        raise ValueError("Required environment variables not configured.")

    try:
        logger.info("Authenticating with Azure using DefaultAzureCredential")
        # Authenticate with Azure
        async with DefaultAzureCredential() as credential:
            # Get Azure AD token for Azure OpenAI
            token = await credential.get_token("https://cognitiveservices.azure.com/.default")
            
            logger.info("Connecting to Azure OpenAI client")
            # Create Azure OpenAI client
            async with AsyncAzureOpenAI(
                azure_endpoint=azure_openai_endpoint,
                azure_ad_token=token.token,
                api_version="2024-10-21"
            ) as openai_client:
                
                logger.info("Generating embeddings for query using model: %s", model_deployment_name)
                # Generate embeddings for the input query
                response = await openai_client.embeddings.create(
                    model=model_deployment_name,
                    input=[query]
                )

                # Ensure the embedding was generated successfully
                if not response.data or not response.data[0].embedding:
                    logger.error("Failed to generate embedding. Response data: %s", response)
                    raise ValueError("Failed to generate embedding.")

                # Extract the embedding vector
                query_vector = response.data[0].embedding
                logger.info("Successfully generated embedding vector of length: %d", len(query_vector))

                # Perform vector search in Cosmos DB with the generated embedding
                logger.info("Querying Cosmos DB for similar snippets")
                results = await cosmos_ops.query_similar_snippets(
                    query_vector=query_vector,
                    project_id=project_id,
                    k=k
                )
                logger.info("Found %d similar snippets", len(results))

                # Return the search results as a JSON string
                return json.dumps(results)

    except Exception as e:
        # Log any errors and return an error payload
        logger.error("Vector search failed with error: %s", str(e), exc_info=True)
        return json.dumps({"error": str(e)})
    finally:
        # Close Cosmos DB connections to clean up resources
        logger.info("Closing Cosmos DB connections")
        await cosmos_ops.close_connections() 