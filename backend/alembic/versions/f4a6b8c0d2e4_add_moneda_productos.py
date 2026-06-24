"""add moneda to productos

Revision ID: f4a6b8c0d2e4
Revises: e3f5a7b9c1d2
Create Date: 2026-06-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a6b8c0d2e4"
down_revision: Union[str, None] = "e3f5a7b9c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("moneda", sa.String(length=3), nullable=False, server_default="ARS"),
    )
    op.alter_column("productos", "moneda", server_default=None)


def downgrade() -> None:
    op.drop_column("productos", "moneda")
