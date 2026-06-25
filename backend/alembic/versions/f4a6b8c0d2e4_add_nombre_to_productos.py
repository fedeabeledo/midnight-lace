"""add nombre to productos

Revision ID: f4a6b8c0d2e4
Revises: e3f5a7b9c1d2
Create Date: 2026-06-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f4a6b8c0d2e4"
down_revision: Union[str, None] = "e3f5a7b9c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "productos",
        sa.Column("nombre", sa.String(length=80), nullable=True),
    )

    op.execute(
        r"""
        UPDATE productos
        SET nombre = CASE
            WHEN "descripcionCatalogo" IS NULL
              OR btrim("descripcionCatalogo") = ''
              OR btrim("descripcionCatalogo") = 'No Posee'
            THEN 'Producto #' || identificador::text
            ELSE btrim(split_part("descripcionCatalogo", E'\n', 1))
        END
        """
    )

    op.execute(
        r"""
        UPDATE productos
        SET "descripcionCatalogo" = CASE
            WHEN "descripcionCatalogo" IS NULL
              OR btrim("descripcionCatalogo") = ''
              OR btrim("descripcionCatalogo") = 'No Posee'
            THEN NULL
            WHEN position(E'\n' in "descripcionCatalogo") > 0
            THEN NULLIF(
                btrim(substring(
                    "descripcionCatalogo"
                    from position(E'\n' in "descripcionCatalogo") + 1
                )),
                ''
            )
            ELSE "descripcionCatalogo"
        END
        """
    )

    op.alter_column("productos", "nombre", nullable=False)


def downgrade() -> None:
    op.execute(
        r"""
        UPDATE productos
        SET "descripcionCatalogo" = CASE
            WHEN "descripcionCatalogo" IS NULL OR btrim("descripcionCatalogo") = ''
            THEN nombre
            ELSE nombre || E'\n' || "descripcionCatalogo"
        END
        WHERE nombre IS NOT NULL
        """
    )
    op.drop_column("productos", "nombre")
