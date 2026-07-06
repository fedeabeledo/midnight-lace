"""normalize subasta estados

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-06 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE subastas SET estado = 'abierta' WHERE estado = 'en curso'")
    op.execute("UPDATE subastas SET estado = 'cerrada' WHERE estado = 'finalizada'")


def downgrade() -> None:
    op.execute("UPDATE subastas SET estado = 'en curso' WHERE estado = 'abierta'")
    op.execute("UPDATE subastas SET estado = 'finalizada' WHERE estado = 'cerrada'")
