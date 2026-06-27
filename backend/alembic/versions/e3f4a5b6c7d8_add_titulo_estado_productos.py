"""add titulo and estado to productos

Revision ID: e3f4a5b6c7d8
Revises: b7c8d9e0f1a2
Create Date: 2026-06-21 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("titulo", sa.String(length=200), nullable=False, server_default="Sin titulo"),
    )
    op.add_column(
        "productos",
        sa.Column("estado", sa.String(length=5), nullable=False, server_default="usado"),
    )
    op.create_check_constraint(
        "chk_estado_producto_condicion",
        "productos",
        "estado IN ('nuevo', 'usado')",
    )
    op.alter_column("productos", "titulo", server_default=None)
    op.alter_column("productos", "estado", server_default=None)


def downgrade() -> None:
    op.drop_constraint("chk_estado_producto_condicion", "productos", type_="check")
    op.drop_column("productos", "estado")
    op.drop_column("productos", "titulo")
