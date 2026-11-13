from dataclasses import FrozenInstanceError

import pytest

from sameplate.domain.recipes.exceptions import InvalidIngredientName
from sameplate.domain.recipes.value_objects import IngredientName


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("  ПоМИДор  ", "помидор"),
        ("Куриное\t  филе\n", "куриное филе"),
        ("\u00a0Томат\u00a0", "томат"),
        ("томаты", "томаты"),
        ("a" * 150, "a" * 150),
    ],
)
def test_normalize_ingredient_name(value: str, expected: str):
    assert IngredientName(value).value == expected
    assert IngredientName(expected).value == expected


@pytest.mark.parametrize("value", ["", " \t\n", "a" * 151])
def test_invalid_ingredient_name(value: str):
    with pytest.raises(InvalidIngredientName):
        IngredientName(value)


def test_ingredient_name_has_value_equality_and_is_immutable():
    name = IngredientName(" Помидор ")
    assert name == IngredientName("помидор")
    assert hash(name) == hash(IngredientName("помидор"))
    with pytest.raises(FrozenInstanceError):
        name.value = "томат"
