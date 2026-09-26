from google.adk.models.lite_llm import LiteLlm

from src.services.storage.products_service import ProductsService
from src.services.storage.weaviate_storage_service import WeaviateStorageService

AZURE_AI_FOUNDRY_MODEL = LiteLlm(model="azure/gpt-4o")

weaviate_storage = WeaviateStorageService()
products_service = ProductsService(storage=weaviate_storage)
