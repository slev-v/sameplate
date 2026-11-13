"""Add ingredient search names and backfill canonical names.

Revision ID: 92a731b8f2d0
Revises: c8f8720eb8fc
"""

import sqlalchemy as sa
from alembic import op

revision = "92a731b8f2d0"
down_revision = "c8f8720eb8fc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_context().as_sql:
        raise RuntimeError("Ingredient name backfill requires an online migration")
    # Keep this normalization local: historical migrations must remain stable.
    connection = op.get_bind()
    rows = connection.execute(sa.text("SELECT id, name FROM ingredients ORDER BY id"))
    names = {}
    records = []
    for ingredient_id, original in rows:
        normalized = " ".join(original.split()).casefold()
        if not normalized or len(normalized) > 150:
            raise ValueError(f"Invalid name for ingredient {ingredient_id}")
        if normalized in names:
            raise ValueError(
                f"Ingredients {names[normalized]} and {ingredient_id} have "
                f"the same normalized name {normalized!r}; resolve before migrating"
            )
        names[normalized] = ingredient_id
        records.append({"ingredient_id": ingredient_id, "name": normalized})

    table = op.create_table(
        "ingredient_names",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingredient_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.CheckConstraint(
            "length(trim(name)) > 0", name=op.f("ck_ingredient_names_nonempty_name")
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
            name=op.f("fk_ingredient_names_ingredient_id_ingredients"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingredient_names")),
        sa.UniqueConstraint("name", name=op.f("uq_ingredient_names_name")),
    )
    op.create_index(
        op.f("ix_ingredient_names_ingredient_id"), "ingredient_names", ["ingredient_id"]
    )
    if records:
        op.bulk_insert(table, records)


def downgrade() -> None:
    op.drop_table("ingredient_names")
