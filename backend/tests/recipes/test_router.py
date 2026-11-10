from decimal import Decimal

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_list_recipes_empty(client: AsyncClient):
    response = await client.get("/api/v1/recipes")

    assert response.status_code == 200
    assert response.json() == []


async def test_list_recipes_pagination(client: AsyncClient, recipe_ids: dict[str, int]):
    response = await client.get("/api/v1/recipes", params={"limit": 1, "offset": 1})

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == recipe_ids["slow_easy_main"]
    assert data[0]["title"] == "Second recipe"


@pytest.mark.parametrize("max_time_minutes", [15, 20])
async def test_list_recipes_time_filter(
    client: AsyncClient, recipe_ids: dict[str, int], max_time_minutes: int
):
    response = await client.get(
        "/api/v1/recipes", params={"max_time_minutes": max_time_minutes}
    )

    assert response.status_code == 200

    data = response.json()
    assert [recipe["id"] for recipe in data] == [
        recipe_ids["quick_easy_main"],
        recipe_ids["quick_medium_main"],
        recipe_ids["quick_easy_salad"],
    ]


async def test_list_recipes_dish_type_filter(
    client: AsyncClient, recipe_ids: dict[str, int]
):
    response = await client.get("/api/v1/recipes", params={"dish_type": "main"})

    assert response.status_code == 200

    data = response.json()
    assert [recipe["id"] for recipe in data] == [
        recipe_ids["quick_easy_main"],
        recipe_ids["slow_easy_main"],
        recipe_ids["quick_medium_main"],
    ]


@pytest.mark.parametrize(
    ("max_difficulty", "expected_keys"),
    [
        (
            "easy",
            ["quick_easy_main", "slow_easy_main", "quick_easy_salad"],
        ),
        (
            "medium",
            [
                "quick_easy_main",
                "slow_easy_main",
                "quick_medium_main",
                "quick_easy_salad",
            ],
        ),
        (
            "hard",
            [
                "quick_easy_main",
                "slow_easy_main",
                "quick_medium_main",
                "quick_easy_salad",
                "slow_hard_soup",
            ],
        ),
    ],
)
async def test_list_recipes_difficulty_filter(
    client: AsyncClient,
    recipe_ids: dict[str, int],
    max_difficulty: str,
    expected_keys: list[str],
):
    response = await client.get(
        "/api/v1/recipes",
        params={"max_difficulty": max_difficulty},
    )

    assert response.status_code == 200

    actual_ids = [recipe["id"] for recipe in response.json()]
    expected_ids = [recipe_ids[key] for key in expected_keys]

    assert actual_ids == expected_ids


async def test_list_recipe_all_filters(client: AsyncClient, recipe_ids: dict[str, int]):
    response = await client.get(
        "/api/v1/recipes",
        params={"max_time_minutes": 20, "max_difficulty": "easy", "dish_type": "main"},
    )

    assert response.status_code == 200

    assert [recipe["id"] for recipe in response.json()] == [
        recipe_ids["quick_easy_main"]
    ]


async def test_get_recipe_with_ingredients(
    client: AsyncClient, recipe_ids: dict[str, int]
):
    recipe_id = recipe_ids["quick_easy_main"]
    response = await client.get(f"/api/v1/recipes/{recipe_id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == recipe_id
    assert data["instructions"] == "Cook your dish"
    assert len(data["ingredients"]) == 1

    ingredient = data["ingredients"][0]
    assert ingredient["name"] == "flour"
    assert Decimal(ingredient["quantity"]) == Decimal("0.500")
    assert ingredient["unit"] == "tbsp"
    assert ingredient["note"] is None
    assert ingredient["is_required"] is True


async def test_get_recipe_not_found(client: AsyncClient):
    response = await client.get("/api/v1/recipes/234234")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_list_recipes_invalid_pagination(
    client: AsyncClient, params: dict[str, int]
):
    response = await client.get("/api/v1/recipes", params=params)

    assert response.status_code == 422
