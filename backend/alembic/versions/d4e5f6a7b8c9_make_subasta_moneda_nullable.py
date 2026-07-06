"""make subasta moneda nullable

Revision ID: d4e5f6a7b8c9
Revises: c2d3e4f5a6b7
Create Date: 2026-07-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "subastas",
        "moneda",
        existing_type=sa.String(length=3),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE subastas SET moneda = 'ARS' WHERE moneda IS NULL")
    op.alter_column(
        "subastas",
        "moneda",
        existing_type=sa.String(length=3),
        nullable=False,
    )
