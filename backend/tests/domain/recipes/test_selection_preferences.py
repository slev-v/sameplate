from dataclasses import FrozenInstanceError

import pytest

from sameplate.domain.recipes.enums import SelectionModeEnum
from sameplate.domain.recipes.exceptions import InvalidSelectionPreferences
from sameplate.domain.recipes.value_objects import SelectionPreferences


def test_explore_has_no_pantry_preferences():
    preferences = SelectionPreferences(mode=SelectionModeEnum.EXPLORE)
    assert preferences.ingredient_ids == frozenset()
    assert preferences.max_missing_ingredients is None


def test_pantry_defaults_to_no_missing_ingredients():
    preferences = SelectionPreferences(
        mode=SelectionModeEnum.PANTRY, ingredient_ids=frozenset({1})
    )
    assert preferences.max_missing_ingredients == 0
    with pytest.raises(FrozenInstanceError):
        preferences.max_missing_ingredients = 2


@pytest.mark.parametrize("limit", [0, 1, 2])
def test_pantry_accepts_missing_ingredient_limits(limit: int):
    preferences = SelectionPreferences(
        mode=SelectionModeEnum.PANTRY,
        ingredient_ids=frozenset({1}),
        max_missing_ingredients=limit,
    )
    assert preferences.max_missing_ingredients == limit


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": SelectionModeEnum.PANTRY},
        {"mode": SelectionModeEnum.PANTRY, "ingredient_ids": frozenset({0})},
        {"mode": SelectionModeEnum.PANTRY, "ingredient_ids": frozenset({-1})},
        {"mode": SelectionModeEnum.PANTRY, "ingredient_ids": frozenset({True})},
        {
            "mode": SelectionModeEnum.PANTRY,
            "ingredient_ids": frozenset({1}),
            "max_missing_ingredients": -1,
        },
        {
            "mode": SelectionModeEnum.PANTRY,
            "ingredient_ids": frozenset({1}),
            "max_missing_ingredients": 3,
        },
        {"mode": SelectionModeEnum.EXPLORE, "ingredient_ids": frozenset({1})},
        {"mode": SelectionModeEnum.EXPLORE, "max_missing_ingredients": 0},
    ],
)
def test_reject_inconsistent_preferences(kwargs):
    with pytest.raises(InvalidSelectionPreferences):
        SelectionPreferences(**kwargs)
