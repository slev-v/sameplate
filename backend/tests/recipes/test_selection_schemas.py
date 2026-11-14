import pytest
from pydantic import TypeAdapter, ValidationError

from sameplate.domain.recipes.enums import (
    DifficultyEnum,
    DishTypeEnum,
    SelectionModeEnum,
)
from sameplate.presentation.api.recipe_selections.schemas import (
    ExploreSelectionRequest,
    PantrySelectionRequest,
    RecipeSelectionRequest,
)


@pytest.fixture
def selection_adapter():
    return TypeAdapter(RecipeSelectionRequest)


def test_pantry_request_converts_to_application_dto(selection_adapter):
    request = selection_adapter.validate_python(
        {
            "mode": "pantry",
            "ingredient_ids": [7, 3, 7],
            "max_missing_ingredients": 2,
            "max_time_minutes": 30,
            "max_difficulty": "medium",
            "dish_type": "main",
            "limit": 5,
        }
    )
    assert isinstance(request, PantrySelectionRequest)
    dto = request.to_dto()
    assert dto.preferences.mode == SelectionModeEnum.PANTRY
    assert dto.preferences.ingredient_ids == frozenset({3, 7})
    assert dto.preferences.max_missing_ingredients == 2
    assert dto.max_time_minutes == 30
    assert dto.max_difficulty == DifficultyEnum.MEDIUM
    assert dto.dish_type == DishTypeEnum.MAIN
    assert dto.limit == 5


def test_pantry_default_missing_limit(selection_adapter):
    request = selection_adapter.validate_python(
        {"mode": "pantry", "ingredient_ids": [1]}
    )
    assert request.to_dto().preferences.max_missing_ingredients == 0


def test_explore_request_defaults(selection_adapter):
    request = selection_adapter.validate_python({"mode": "explore"})
    assert isinstance(request, ExploreSelectionRequest)
    dto = request.to_dto()
    assert dto.preferences.mode == SelectionModeEnum.EXPLORE
    assert dto.preferences.ingredient_ids == frozenset()
    assert dto.preferences.max_missing_ingredients is None
    assert dto.limit == 20


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"mode": "unknown"},
        {"mode": "pantry"},
        {"mode": "pantry", "ingredient_ids": []},
        {"mode": "pantry", "ingredient_ids": [0]},
        {"mode": "pantry", "ingredient_ids": [2_147_483_648]},
        {"mode": "pantry", "ingredient_ids": [True]},
        {"mode": "pantry", "ingredient_ids": [1], "max_missing_ingredients": -1},
        {"mode": "pantry", "ingredient_ids": [1], "max_missing_ingredients": 3},
        {"mode": "explore", "ingredient_ids": []},
        {"mode": "explore", "max_missing_ingredients": None},
        {"mode": "explore", "limit": 0},
        {"mode": "explore", "limit": 21},
        {"mode": "explore", "max_time_minutes": 0},
        {"mode": "explore", "max_difficulty": "unknown"},
        {"mode": "explore", "offset": 0},
    ],
)
def test_reject_invalid_selection_request(selection_adapter, data):
    with pytest.raises(ValidationError):
        selection_adapter.validate_python(data)
