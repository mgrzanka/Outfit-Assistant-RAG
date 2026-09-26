import json
import os


def create_value_tuple(values: list[str]) -> tuple[str, ...]:
    """Creates a tuple from a list of values with an OTHER fallback."""
    unique_values = list(set(values))
    if "OTHER" not in unique_values:
        unique_values.append("OTHER")
    return tuple(unique_values)


def normalize_material_key(material_name: str) -> str:
    """Normalizes material names to match Weaviate property names."""
    return "_".join(material_name.lower().split())


def _load_unique_values() -> dict:
    """Loads unique feature values from ./data/unique_values.json"""
    json_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "unique_values.json"
    )

    if not os.path.exists(json_path):
        raise FileNotFoundError(
            f"Required file not found: {json_path}\n"
            "Run the data preparation notebook to generate unique_values.json"
        )

    with open(json_path, "r") as f:
        uniques = json.load(f)

    required_keys = ["sizes", "sex", "materials", "construction"]
    missing_keys = [key for key in required_keys if key not in uniques]
    if missing_keys:
        raise ValueError(
            f"unique_values.json is missing required keys: {', '.join(missing_keys)}"
        )

    uniques["materials"] = [
        normalize_material_key(m) for m in uniques.get("materials", [])
    ]

    return uniques


_unique_values = _load_unique_values()

SIZES = create_value_tuple(_unique_values.get("sizes", []))
SEXES = create_value_tuple(_unique_values.get("sex", []))
MATERIALS = create_value_tuple(_unique_values.get("materials", []))
CONSTRUCTIONS = create_value_tuple(_unique_values.get("constructions", []))


__all__ = [
    "SIZES",
    "SEXES",
    "MATERIALS",
    "CONSTRUCTIONS",
]
