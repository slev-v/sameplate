from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.domain.recipes.value_objects import IngredientName
from sameplate.infrastructure.db.models.recipes import IngredientNameModel


class SqlAlchemyIngredientNameRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def assign_name(self, ingredient_id: int, name: IngredientName) -> bool:
        statement = (
            insert(IngredientNameModel)
            .values(ingredient_id=ingredient_id, name=name.value)
            .on_conflict_do_nothing(index_elements=[IngredientNameModel.name])
            .returning(IngredientNameModel.id)
        )
        if await self._session.scalar(statement) is not None:
            return True

        owner_id = await self._session.scalar(
            select(IngredientNameModel.ingredient_id).where(
                IngredientNameModel.name == name.value
            )
        )
        return owner_id == ingredient_id
