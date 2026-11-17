"""Añade observaciones a libros

Revision ID: 6133bce43e8c
Revises:
Create Date: 2026-11-15 20:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6133bce43e8c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "libros",
        sa.Column("observaciones", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("libros", "observaciones")