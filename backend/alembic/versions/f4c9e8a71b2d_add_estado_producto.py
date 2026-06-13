"""add estado to productos

Revision ID: f4c9e8a71b2d
Revises: a1b2c3d4e5f6
Create Date: 2026-06-12 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4c9e8a71b2d"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("estado", sa.String(length=5), server_default="usado", nullable=False),
    )
    op.create_check_constraint(
        "ck_productos_estado",
        "productos",
        "estado IN ('nuevo', 'usado')",
    )
    op.alter_column("productos", "estado", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_productos_estado", "productos", type_="check")
    op.drop_column("productos", "estado")
