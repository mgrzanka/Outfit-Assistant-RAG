from weaviate.classes.query import Filter

from src.models.filter_models import Filters
from src.services.storage.weaviate_storage_service import WeaviateStorageService


class ProductsService:
    def __init__(self, storage: WeaviateStorageService) -> None:
        self._storage = storage
        self._collection_name = "Products"

    def product_search(self, query: str, filters: Filters) -> dict:
        """
        Searches for products using semantic search + structured filters.

        Args:
            query: Natural language search query (e.g., "white party dress")
            filters: Structured filters from Filters model

        Returns:
            dict with 'message' (str) and 'search_results' (list of product dicts)
        """
        weaviate_filters = self._build_weaviate_filters(filters)

        # Execute search with filters
        response = self._storage.search(
            collection_name=self._collection_name,
            query=query,
            filters=weaviate_filters,
            limit=5,
        )

        # If no results with filters, retry without filters
        if not response:
            message = "No results after search with filters. Provided results were obtained without the filters."
            response = self._storage.search(
                collection_name=self._collection_name,
                query=query,
                filters=None,
                limit=3,
            )
        else:
            message = (
                "Success in obtaining requested products with given query and filters."
            )

        return {"message": message, "search_results": response}

    def _build_weaviate_filters(self, filters: Filters) -> Filter | None:
        """Translates Filters model to Weaviate Filter objects."""
        weaviate_filters = []

        # Sex
        if filters.sex and filters.sex != "OTHER":
            weaviate_filters.append(Filter.by_property("sex").equal(filters.sex))

        # Construction (garment type)
        if filters.construction and filters.construction != "OTHER":
            weaviate_filters.append(
                Filter.by_property("construction").equal(filters.construction)
            )

        # Sizes
        if filters.sizes:
            size_values = [s for s in filters.sizes if s != "OTHER"]
            if size_values:
                weaviate_filters.append(
                    Filter.by_property("sizes").contains_any(size_values)
                )

        # Color
        if filters.color:
            weaviate_filters.append(Filter.by_property("color").equal(filters.color))

        # Price
        if filters.price:
            if filters.price.operator == "gt":
                weaviate_filters.append(
                    Filter.by_property("price_pln").greater_than(filters.price.value)
                )
            elif filters.price.operator == "lt":
                weaviate_filters.append(
                    Filter.by_property("price_pln").less_than(filters.price.value)
                )
            elif filters.price.operator == "eq":
                weaviate_filters.append(
                    Filter.by_property("price_pln").equal(filters.price.value)
                )

        # Material
        if filters.materials:
            for mat in filters.materials:
                if mat.key == "OTHER":
                    continue

                material_property = mat.get_weaviate_property_name()

                if mat.operator == "exists":
                    weaviate_filters.append(
                        Filter.by_property(material_property).greater_than(0)
                    )
                elif mat.operator == "eq" and mat.percentage is not None:
                    weaviate_filters.append(
                        Filter.by_property(material_property).equal(mat.percentage)
                    )
                elif mat.operator == "gt" and mat.percentage is not None:
                    weaviate_filters.append(
                        Filter.by_property(material_property).greater_than(
                            mat.percentage
                        )
                    )
                elif mat.operator == "lt" and mat.percentage is not None:
                    weaviate_filters.append(
                        Filter.by_property(material_property).less_than(mat.percentage)
                    )
                else:
                    weaviate_filters.append(
                        Filter.by_property(material_property).greater_than(0)
                    )

        combined_filter = None
        if weaviate_filters:
            combined_filter = weaviate_filters[0]
            for f in weaviate_filters[1:]:
                combined_filter = combined_filter & f

        return combined_filter
