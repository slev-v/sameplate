from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from sameplate.application.recipes.dto import RecipeSelectionRequestDTO
from sameplate.domain.recipes.enums import (
    DifficultyEnum,
    DishTypeEnum,
    SelectionModeEnum,
)
from sameplate.domain.recipes.value_objects import SelectionPreferences


class _SelectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_time_minutes: int | None = Field(default=None, gt=0, le=2_147_483_647)
    max_difficulty: DifficultyEnum | None = None
    dish_type: DishTypeEnum | None = None
    limit: int = Field(default=20, ge=1, le=20)

    def _to_dto(self, preferences: SelectionPreferences) -> RecipeSelectionRequestDTO:
        return RecipeSelectionRequestDTO(
            preferences=preferences,
            max_time_minutes=self.max_time_minutes,
            max_difficulty=self.max_difficulty,
            dish_type=self.dish_type,
            limit=self.limit,
        )


class PantrySelectionRequest(_SelectionRequest):
    mode: Literal[SelectionModeEnum.PANTRY]
    ingredient_ids: frozenset[
        Annotated[int, Field(strict=True, gt=0, le=2_147_483_647)]
    ] = Field(min_length=1)
    max_missing_ingredients: int = Field(default=0, strict=True, ge=0, le=2)

    def to_dto(self) -> RecipeSelectionRequestDTO:
        return self._to_dto(
            SelectionPreferences(
                mode=self.mode,
                ingredient_ids=self.ingredient_ids,
                max_missing_ingredients=self.max_missing_ingredients,
            )
        )


class ExploreSelectionRequest(_SelectionRequest):
    mode: Literal[SelectionModeEnum.EXPLORE]

    def to_dto(self) -> RecipeSelectionRequestDTO:
        return self._to_dto(SelectionPreferences(mode=self.mode))


RecipeSelectionRequest = Annotated[
    PantrySelectionRequest | ExploreSelectionRequest,
    Field(discriminator="mode"),
]
