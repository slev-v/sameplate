from dataclasses import dataclass

from sameplate.domain.recipes.exceptions import InvalidIngredientName


@dataclass(frozen=True, slots=True)
class IngredientName:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvalidIngredientName("Ingredient name must be a string")
        normalized = " ".join(self.value.split()).casefold()
        if not normalized:
            raise InvalidIngredientName("Ingredient name must not be empty")
        if len(normalized) > 150:
            raise InvalidIngredientName(
                "Ingredient name must not exceed 150 characters"
            )
        object.__setattr__(self, "value", normalized)
