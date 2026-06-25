"""add foto principal to subastas

Revision ID: f7d9e1c3a5b7
Revises: f6c8d0e2a4b6
Create Date: 2026-06-25 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "f7d9e1c3a5b7"
down_revision: Union[str, None] = "f6c8d0e2a4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subastas", sa.Column("fotoPrincipal", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("subastas", "fotoPrincipal")
