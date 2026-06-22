"""pagos y registros de subasta

Revision ID: e3f5a7b9c1d2
Revises: b7c8d9e0f1a2
Create Date: 2026-06-17 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3f5a7b9c1d2'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('registroDeSubasta', sa.Column('fechaPago', sa.DateTime(timezone=True), nullable=True))
    op.add_column('registroDeSubasta', sa.Column('fechaVencimiento', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('registroDeSubasta', 'fechaVencimiento')
    op.drop_column('registroDeSubasta', 'fechaPago')
