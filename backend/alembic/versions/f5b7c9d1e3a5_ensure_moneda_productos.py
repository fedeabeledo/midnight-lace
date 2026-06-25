"""ensure moneda on productos

Revision ID: f5b7c9d1e3a5
Revises: f4a6b8c0d2e4
Create Date: 2026-06-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f5b7c9d1e3a5"
down_revision: Union[str, None] = "f4a6b8c0d2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'productos'
                  AND column_name = 'moneda'
            ) THEN
                ALTER TABLE productos
                ADD COLUMN moneda VARCHAR(3) NOT NULL DEFAULT 'ARS';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'productos'
                  AND column_name = 'moneda'
            ) THEN
                ALTER TABLE productos DROP COLUMN moneda;
            END IF;
        END $$;
        """
    )
