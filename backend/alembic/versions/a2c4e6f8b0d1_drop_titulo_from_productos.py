"""drop titulo from productos

Revision ID: a2c4e6f8b0d1
Revises: f9e1b3c5d7a9, e3f4a5b6c7d8
Create Date: 2026-06-27 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a2c4e6f8b0d1"
down_revision: Union[str, Sequence[str], None] = ("f9e1b3c5d7a9", "e3f4a5b6c7d8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'productos'
                  AND column_name = 'titulo'
            ) THEN
                ALTER TABLE productos DROP COLUMN titulo;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'productos'
                  AND column_name = 'titulo'
            ) THEN
                ALTER TABLE productos ADD COLUMN titulo VARCHAR(200);
                UPDATE productos SET titulo = left(nombre, 200);
                ALTER TABLE productos ALTER COLUMN titulo SET NOT NULL;
            END IF;
        END $$;
        """
    )
