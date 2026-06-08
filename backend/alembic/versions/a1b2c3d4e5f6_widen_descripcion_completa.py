"""widen descripcionCompleta to 2000

Revision ID: a1b2c3d4e5f6
Revises: d2b4ba20f8f8
Create Date: 2026-06-08 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d2b4ba20f8f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE productos ALTER COLUMN "descripcionCompleta" TYPE VARCHAR(2000)')


def downgrade() -> None:
    op.execute('ALTER TABLE productos ALTER COLUMN "descripcionCompleta" TYPE VARCHAR(300)')
