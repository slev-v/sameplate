from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from sameplate.application.recipes.ports import IngredientReader, RecipeReader
from sameplate.infrastructure.db.readers.ingredients import SqlAlchemyIngredientReader
from sameplate.infrastructure.db.readers.recipes import SqlAlchemyRecipeReader


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    session_factory: async_sessionmaker[AsyncSession] = (
        request.app.state.session_factory
    )

    async with session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_recipe_reader(session: SessionDep) -> RecipeReader:
    return SqlAlchemyRecipeReader(session)


RecipeReaderDep = Annotated[RecipeReader, Depends(get_recipe_reader)]


def get_ingredient_reader(session: SessionDep) -> IngredientReader:
    return SqlAlchemyIngredientReader(session)


IngredientReaderDep = Annotated[IngredientReader, Depends(get_ingredient_reader)]
