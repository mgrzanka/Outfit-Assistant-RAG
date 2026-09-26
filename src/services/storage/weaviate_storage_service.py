import json
import weaviate
import os


class WeaviateStorageService:
    def search(self,
               collection_name: str,
               limit: int,
               query: str,
               vector_search_percentage: float = 0.75,
               filters = None,
               return_properties: list[str] | None = None
               ):
        """
        Perform a hybrid search query on a given Weaviate collection.
        Args:
            collection (weaviate.collections.Collection):
                The Weaviate collection to perform the search on.
            return_properties (list[str] | None):
                A list of property names to include in the response. If None, all properties are returned.
            vector_search_percentage (float):
                Values closer to 1 prioritize vector similarity; values closer to 0 favor keyword matching.
            limit (int):
                The maximum number of objects to return from the query.
            query (str):
                The textual search query to match against the collection.
            filters (weaviate.classes.query.Filter | None, optional):
                Optional filter expression (constructed via `weaviate.classes.query.Filter`)
                Restrict the search results to matching objects.
        Returns:
            list[str]:
                A list of JSON-formatted strings representing the matching objects'
                properties from the collection.
        Raises:
            Exception with corresponding error message if any error occurs while executing the search query.
        """
        try:
            with self._get_weaviate_client() as client:
                collection = client.collections.use(collection_name)
                search_response = collection.query.hybrid(
                    query=query,
                    filters=filters,
                    alpha=vector_search_percentage,
                    return_properties=return_properties,
                    limit=limit
                )
                search_response_parsed = [obj.properties for obj in search_response.objects]
                return search_response_parsed
        except Exception as e:
            print(f"Error while performing weaviate's search on collection {collection_name}: {str(e)}")
            raise e

    def delete_weaviate_collection(self, collection_name: str) -> None:
        """
        Delete collection with provided collection_name
        Parameters:
            collection_name (str): A string matching name of the collection you want to delete.
        Raises exception with corresponding message if something went wrong during the deletion.
        """
        try:
            with self._get_weaviate_client() as client:
                client.collections.delete(collection_name)
        except Exception as e:
            print(f"Exception while deleting collection {collection_name}: {str(e)}")
            raise e

    def get_weaviate_collection(self, collection_name: str) -> weaviate.collections.Collection:
        """
        Get instance of weaviate collection with provided collection_name
        Parameters:
            collection_name (str): A string matching name of the collection you want to delete.
        Raises:
            Exception with corresponding message if something went wrong during getting the collection from weaviate.
        """
        try:
            with self._get_weaviate_client() as client:
                collection = client.collections.use(collection_name)
                aggregation = collection.aggregate.over_all(total_count=True)

                print(f"Collection {collection_name} with {aggregation.total_count} elements loaded.")

                return collection

        except Exception as e:
                print(f"Error while getting weaviate's collection: {str(e)}")
                raise e

    def _get_weaviate_client(self):
        """
        Tworzy klienta Weaviate z konfiguracją pobraną ze zmiennych środowiskowych.
        Pozwala to na działanie zarówno lokalnie (localhost) jak i w Dockerze (weaviate).
        """
        host = os.getenv("WEAVIATE_HOST", "localhost")
        port = int(os.getenv("WEAVIATE_PORT", 8080))
        grpc_port = int(os.getenv("WEAVIATE_GRPC_PORT", 50051))

        return weaviate.connect_to_custom(
            http_host=host,
            http_port=port,
            http_secure=False,
            grpc_host=host,
            grpc_port=grpc_port,
            grpc_secure=False
        )
