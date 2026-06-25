"""fecha obra texto

Revision ID: f6c8d0e2a4b6
Revises: f5b7c9d1e3a5
Create Date: 2026-06-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = "f6c8d0e2a4b6"
down_revision: Union[str, None] = "f5b7c9d1e3a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE "detalleArtistico"
        ALTER COLUMN "fechaObra" TYPE VARCHAR(80)
        USING "fechaObra"::text
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE "detalleArtistico"
        ALTER COLUMN "fechaObra" TYPE DATE
        USING CASE
            WHEN "fechaObra" ~ '^\\d{4}-\\d{2}-\\d{2}$'
            THEN "fechaObra"::date
            ELSE NULL
        END
        """
    )
