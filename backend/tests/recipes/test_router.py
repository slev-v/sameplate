from decimal import Decimal

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_list_recipes_empty(client: AsyncClient):
    response = await client.get("/api/v1/recipes")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_recipes_pagination(client: AsyncClient, recipe_ids: list[int]):
    response = await client.get("api/v1/recipes", params={"limit": 1, "offset": 1})

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == recipe_ids[1]
    assert data[0]["title"] == "Second recipe"


async def test_get_recipe_with_ingredients(client: AsyncClient, recipe_ids: list[int]):
    response = await client.get(f"api/v1/recipes/{recipe_ids[0]}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == recipe_ids[0]
    assert data["instructions"] == "Cook your dish"
    assert len(data["ingredients"]) == 1

    ingredient = data["ingredients"][0]
    assert ingredient["name"] == "flour"
    assert Decimal(ingredient["quantity"]) == Decimal("0.500")
    assert ingredient["unit"] == "tbsp"
    assert ingredient["note"] is None
    assert ingredient["is_required"] is True


async def test_get_recipe_not_found(client: AsyncClient):
    response = await client.get("api/v1/recipes/234234")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_list_recipes_invalid_pagination(
    client: AsyncClient, params: dict[str, int]
):
    response = await client.get("api/v1/recipes", params=params)

    assert response.status_code == 422
