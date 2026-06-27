"""widen estado producto

Revision ID: f9e1b3c5d7a9
Revises: f8e0a2c4b6d8
Create Date: 2026-06-26 05:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f9e1b3c5d7a9"
down_revision: Union[str, None] = "f8e0a2c4b6d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "productos",
        "estadoProducto",
        existing_type=sa.String(length=15),
        type_=sa.String(length=25),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE productos
        SET "estadoProducto" = 'asignado'
        WHERE length("estadoProducto") > 15
        """
    )
    op.alter_column(
        "productos",
        "estadoProducto",
        existing_type=sa.String(length=25),
        type_=sa.String(length=15),
        existing_nullable=False,
    )
