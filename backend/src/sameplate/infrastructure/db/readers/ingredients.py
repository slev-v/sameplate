from sqlalchemy import and_, func, literal_column, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from sameplate.application.recipes.dto import IngredientDTO, IngredientFilters
from sameplate.infrastructure.db.models.recipes import (
    IngredientModel,
    IngredientNameModel,
)


class SqlAlchemyIngredientReader:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_ingredients(self, filters: IngredientFilters) -> list[IngredientDTO]:
        statement = select(IngredientModel.id, IngredientModel.name)
        if filters.q is not None:
            q = filters.q
            name = func.replace(IngredientNameModel.name, "ё", "е")
            partial_match = and_(
                *(name.contains(word, autoescape=True) for word in q.split())
            )
            language = literal_column("'russian'")
            word_match = func.to_tsvector(language, name).op("@@")(
                func.plainto_tsquery(language, q)
            )
            matching_ids = select(IngredientNameModel.ingredient_id).where(
                or_(partial_match, word_match)
            )
            statement = statement.where(IngredientModel.id.in_(matching_ids))
        statement = (
            statement.order_by(IngredientModel.name, IngredientModel.id)
            .limit(filters.limit)
            .offset(filters.offset)
        )
        rows = await self._session.execute(statement)
        return [IngredientDTO(id=id_, name=name) for id_, name in rows]
