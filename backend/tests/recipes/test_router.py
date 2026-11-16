from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.infrastructure.db.models.recipes import IngredientModel

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
    assert len(data["ingredients"]) == 2

    ingredients = {item["name"]: item for item in data["ingredients"]}
    ingredient = ingredients["flour"]
    assert ingredient["name"] == "flour"
    assert Decimal(ingredient["quantity"]) == Decimal("0.500")
    assert ingredient["unit"] == "tbsp"
    assert ingredient["note"] is None
    assert ingredient["is_required"] is True

    assert ingredients["salt"]["quantity"] is None
    assert ingredients["salt"]["unit"] is None
    assert ingredients["salt"]["note"] == "To taste"
    assert ingredients["salt"]["is_required"] is False


async def test_get_recipe_not_found(client: AsyncClient):
    response = await client.get("/api/v1/recipes/234234")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"offset": 2_147_483_648},
        {"max_time_minutes": 0},
        {"max_time_minutes": 2_147_483_648},
        {"max_difficulty": "unknown"},
        {"dish_type": "unknown"},
    ],
)
async def test_list_recipes_invalid_pagination(
    client: AsyncClient, params: dict[str, int | str]
):
    response = await client.get("/api/v1/recipes", params=params)

    assert response.status_code == 422


@pytest.mark.parametrize("recipe_id", [0, -1, 2_147_483_648])
async def test_get_recipe_invalid_id(client: AsyncClient, recipe_id: int):
    response = await client.get(f"/api/v1/recipes/{recipe_id}")

    assert response.status_code == 422


async def test_filters_without_matches(client: AsyncClient, recipe_ids: dict[str, int]):
    response = await client.get("/api/v1/recipes", params={"max_time_minutes": 10})

    assert response.status_code == 200
    assert response.json() == []


async def test_pantry_mode(
    client: AsyncClient, selection_data: tuple[dict[str, int], frozenset[int]]
):
    recipe_ids, available_ids = selection_data
    response = await client.post(
        "/api/v1/recipe-selections",
        json={
            "mode": "pantry",
            "ingredient_ids": list(available_ids),
            "max_missing_ingredients": 0,
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert [recipe["id"] for recipe in data] == [recipe_ids["complete"]]


async def test_explore_mode(
    client: AsyncClient, selection_data: tuple[dict[str, int], frozenset[int]]
):

    response = await client.post(
        "/api/v1/recipe-selections", json={"mode": "explore", "limit": 2}
    )

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] != data[1]["id"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"mode": "unknown"},
        {"mode": "pantry", "ingredient_ids": []},
        {"mode": "explore", "ingredient_ids": [1]},
        {"mode": "explore", "limit": 0},
    ],
)
async def test_selection_invalid_body(
    client: AsyncClient,
    payload: dict,
):
    response = await client.post("/api/v1/recipe-selections", json=payload)

    assert response.status_code == 422


async def test_selection_unknown_ingredients(
    client: AsyncClient,
    db_session: AsyncSession,
    selection_data: tuple[dict[str, int], frozenset[int]],
):
    max_id = await db_session.scalar(select(func.max(IngredientModel.id)))
    unknown_id = (max_id or 0) + 1

    response = await client.post(
        "/api/v1/recipe-selections",
        json={"mode": "pantry", "ingredient_ids": [unknown_id]},
    )

    assert response.status_code == 422

    data = response.json()
    assert data["detail"]["ingredient_ids"] == [unknown_id]


async def test_selection_no_matches(
    client: AsyncClient,
    selection_data: tuple[dict[str, int], frozenset[int]],
):
    response = await client.post(
        "/api/v1/recipe-selections",
        json={
            "mode": "explore",
            "max_time_minutes": 10,
        },
    )

    assert response.status_code == 200
    assert response.json() == []
