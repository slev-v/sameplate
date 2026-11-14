from dataclasses import dataclass

from sameplate.domain.recipes.enums import SelectionModeEnum
from sameplate.domain.recipes.exceptions import (
    InvalidIngredientName,
    InvalidSelectionPreferences,
)


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


@dataclass(frozen=True, slots=True)
class SelectionPreferences:
    mode: SelectionModeEnum
    ingredient_ids: frozenset[int] = frozenset()
    max_missing_ingredients: int | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "ingredient_ids", frozenset(self.ingredient_ids))
        if any(type(id_) is not int or id_ <= 0 for id_ in self.ingredient_ids):
            raise InvalidSelectionPreferences(
                "Ingredient IDs must be positive integers"
            )
        if self.mode == SelectionModeEnum.EXPLORE:
            if self.ingredient_ids or self.max_missing_ingredients is not None:
                raise InvalidSelectionPreferences(
                    "Explore does not accept pantry preferences"
                )
        elif self.mode == SelectionModeEnum.PANTRY:
            if not self.ingredient_ids:
                raise InvalidSelectionPreferences(
                    "Pantry requires at least one ingredient"
                )
            if self.max_missing_ingredients is None:
                object.__setattr__(self, "max_missing_ingredients", 0)
            elif (
                type(self.max_missing_ingredients) is not int
                or not 0 <= self.max_missing_ingredients <= 2
            ):
                raise InvalidSelectionPreferences(
                    "Missing ingredient limit must be 0, 1 or 2"
                )
        else:
            raise InvalidSelectionPreferences("Unknown selection mode")
