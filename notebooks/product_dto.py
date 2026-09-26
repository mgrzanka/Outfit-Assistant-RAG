from dataclasses import dataclass

@dataclass
class Price:
    value: float
    currency: str

@dataclass
class Material:
    name: str
    percentage: int

    def __str__(self):
        return f"{self.name}: {self.percentage}"

@dataclass
class ProductDto:
    name: str
    description: str
    color: str
    construction: str
    materials: list[Material]
    price: Price
    sizes: list[str]
    sex: str
    image_url: str

    def to_rag_string(self):
        description_builder = [
            f"PRODUCT: {self.name}", f"DESCRIPTION: {self.description}", f"COLOR: {self.color}"
        ]
        if self.construction is not None:
            description_builder.append(f"CONSTRUCTION: {self.construction}")

        if self.materials:
            description_builder.append(f"MATERIALS: {' '.join([str(m) for m in self.materials if m.percentage > 0])}")

        return "\n".join(description_builder)
