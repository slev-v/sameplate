import pytest

from sameplate.application.recipes.use_cases import register_ingredient_name
from sameplate.domain.recipes.exceptions import (
    IngredientNameConflict,
    InvalidIngredientName,
)
from sameplate.domain.recipes.value_objects import IngredientName

pytestmark = pytest.mark.asyncio


class InMemoryIngredientNameRepository:
    def __init__(self) -> None:
        self.owners: dict[str, int] = {}

    async def assign_name(self, ingredient_id: int, name: IngredientName) -> bool:
        return self.owners.setdefault(name.value, ingredient_id) == ingredient_id


async def test_register_name_normalizes_and_is_idempotent():
    repository = InMemoryIngredientNameRepository()

    await register_ingredient_name(1, " ТОМАТ ", repository=repository)
    await register_ingredient_name(1, "томат", repository=repository)

    assert repository.owners == {"томат": 1}


async def test_register_name_rejects_another_owner():
    repository = InMemoryIngredientNameRepository()
    await register_ingredient_name(1, "томат", repository=repository)

    with pytest.raises(IngredientNameConflict):
        await register_ingredient_name(2, "томат", repository=repository)

    assert repository.owners == {"томат": 1}


async def test_invalid_name_is_not_registered():
    repository = InMemoryIngredientNameRepository()

    with pytest.raises(InvalidIngredientName):
        await register_ingredient_name(1, "  ", repository=repository)

    assert repository.owners == {}
