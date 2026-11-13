from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, Text, true
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sameplate.domain.recipes.enums import DifficultyEnum, DishTypeEnum, UnitEnum
from sameplate.infrastructure.db.base import Base


class RecipeModel(Base):
    __tablename__ = "recipes"

    __table_args__ = (
        CheckConstraint(
            "cooking_time_minutes > 0",
            name="positive_cooking_time",
        ),
        CheckConstraint(
            "servings > 0",
            name="positive_servings",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(String(500))
    instructions: Mapped[str] = mapped_column(Text)

    cooking_time_minutes: Mapped[int] = mapped_column()

    difficulty: Mapped[DifficultyEnum] = mapped_column(
        SAEnum(
            DifficultyEnum,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="difficulty",
        )
    )

    dish_type: Mapped[DishTypeEnum] = mapped_column(
        SAEnum(
            DishTypeEnum,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="dish_type",
        )
    )

    servings: Mapped[int] = mapped_column()
    image_url: Mapped[str | None] = mapped_column()

    ingredient_links: Mapped[list[RecipeIngredientModel]] = relationship(
        back_populates="recipe",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class IngredientModel(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)

    names: Mapped[list[IngredientNameModel]] = relationship(
        back_populates="ingredient",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class IngredientNameModel(Base):
    __tablename__ = "ingredient_names"
    __table_args__ = (CheckConstraint("length(trim(name)) > 0", name="nonempty_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150), unique=True)

    ingredient: Mapped[IngredientModel] = relationship(back_populates="names")


class RecipeIngredientModel(Base):
    __tablename__ = "recipe_ingredients"

    __table_args__ = (
        CheckConstraint(
            "quantity IS NULL OR quantity > 0",
            name="positive_quantity",
        ),
        CheckConstraint(
            "(quantity IS NULL AND unit IS NULL) OR "
            "(quantity IS NOT NULL AND unit IS NOT NULL)",
            name="quantity_unit_pair",
        ),
    )

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"), primary_key=True
    )

    quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 3))

    unit: Mapped[UnitEnum | None] = mapped_column(
        SAEnum(
            UnitEnum,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="unit",
        ),
    )
    note: Mapped[str | None] = mapped_column(String(250))
    is_required: Mapped[bool] = mapped_column(
        default=True,
        server_default=true(),
    )

    recipe: Mapped[RecipeModel] = relationship(
        back_populates="ingredient_links",
    )
    ingredient: Mapped[IngredientModel] = relationship()
