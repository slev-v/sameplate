import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.use_cases import register_ingredient_name
from sameplate.infrastructure.db.models.recipes import IngredientModel
from sameplate.infrastructure.db.repositories.ingredient_names import (
    SqlAlchemyIngredientNameRepository,
)

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def ingredient_ids(db_session: AsyncSession) -> dict[str, int]:
    data = {
        "яйцо": [],
        "помидор": ["томат"],
        "твёрдый сыр": [],
        "морковь": ["морковка"],
        "пшеничная мука": [],
        "картофель": ["картошка"],
    }
    repository = SqlAlchemyIngredientNameRepository(db_session)
    ids = {}
    for name, synonyms in data.items():
        ingredient = IngredientModel(name=name)
        db_session.add(ingredient)
        await db_session.flush()
        ids[name] = ingredient.id
        for search_name in [name, *synonyms]:
            await register_ingredient_name(
                ingredient.id, search_name, repository=repository
            )
    return ids


async def test_empty_catalog(client: AsyncClient):
    response = await client.get("/api/v1/ingredients")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize("q", [None, "", " \t "])
async def test_catalog_order_and_response(
    client: AsyncClient, ingredient_ids: dict[str, int], q: str | None
):
    response = await client.get(
        "/api/v1/ingredients", params={} if q is None else {"q": q}
    )
    assert response.status_code == 200
    assert response.json() == [
        {"id": ingredient_ids[name], "name": name}
        for name in [
            "картофель",
            "морковь",
            "помидор",
            "пшеничная мука",
            "твёрдый сыр",
            "яйцо",
        ]
    ]


@pytest.mark.parametrize(
    ("q", "expected_name"),
    [
        ("помидор", "помидор"),
        ("томат", "помидор"),
        ("том", "помидор"),
        ("  ТоМаТ \t", "помидор"),
        ("помидоры", "помидор"),
        ("томатами", "помидор"),
        ("яйца", "яйцо"),
        ("морковью", "морковь"),
        ("мор", "морковь"),
        ("мука пшеничная", "пшеничная мука"),
        ("  МУК  пшен ", "пшеничная мука"),
        ("твердый сыр", "твёрдый сыр"),
        ("твёрдый сыр", "твёрдый сыр"),
    ],
)
async def test_search_returns_canonical_ingredient_once(
    client: AsyncClient,
    ingredient_ids: dict[str, int],
    q: str,
    expected_name: str,
):
    response = await client.get("/api/v1/ingredients", params={"q": q})
    assert response.status_code == 200
    assert response.json() == [
        {"id": ingredient_ids[expected_name], "name": expected_name}
    ]


@pytest.mark.parametrize("q", ["несуществующий продукт", "%", "_"])
async def test_no_matches_and_literal_wildcards(
    client: AsyncClient, ingredient_ids: dict[str, int], q: str
):
    response = await client.get("/api/v1/ingredients", params={"q": q})
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"limit": 2, "offset": 1}, ["морковь", "помидор"]),
        ({"q": "мор", "limit": 1, "offset": 1}, []),
        ({"q": "помидор", "limit": 1}, ["помидор"]),
        ({"offset": 100}, []),
    ],
)
async def test_pagination(
    client: AsyncClient,
    ingredient_ids: dict[str, int],
    params: dict[str, str | int],
    expected: list[str],
):
    response = await client.get("/api/v1/ingredients", params=params)
    assert response.status_code == 200
    assert response.json() == [
        {"id": ingredient_ids[name], "name": name} for name in expected
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"offset": 2_147_483_648},
        {"q": "a" * 151},
        {"q": "ß" * 100},
    ],
)
async def test_invalid_query_parameters(
    client: AsyncClient, params: dict[str, str | int]
):
    response = await client.get("/api/v1/ingredients", params=params)
    assert response.status_code == 422
