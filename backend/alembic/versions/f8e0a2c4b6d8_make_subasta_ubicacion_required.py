"""make subasta ubicacion required

Revision ID: f8e0a2c4b6d8
Revises: f7d9e1c3a5b7
Create Date: 2026-06-26 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f8e0a2c4b6d8"
down_revision: Union[str, None] = "f7d9e1c3a5b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


FALLBACK_UBICACION = "Ubicacion a confirmar"


def upgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE subastas SET ubicacion = :fallback "
            "WHERE ubicacion IS NULL OR btrim(ubicacion) = ''"
        ).bindparams(fallback=FALLBACK_UBICACION)
    )
    op.alter_column(
        "subastas",
        "ubicacion",
        existing_type=sa.String(length=350),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "subastas",
        "ubicacion",
        existing_type=sa.String(length=350),
        nullable=True,
    )
