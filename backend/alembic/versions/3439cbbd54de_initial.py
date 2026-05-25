"""initial

Revision ID: 3439cbbd54de
Revises:
Create Date: 2026-05-24 18:10:12.797332
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3439cbbd54de'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tablas sin dependencias primero
    op.create_table('paises',
        sa.Column('numero', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=250), nullable=False),
        sa.Column('nombreCorto', sa.String(length=250), nullable=True),
        sa.Column('capital', sa.String(length=250), nullable=False),
        sa.Column('nacionalidad', sa.String(length=250), nullable=False),
        sa.Column('idiomas', sa.String(length=150), nullable=False),
        sa.PrimaryKeyConstraint('numero')
    )
    op.create_table('personas',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('documento', sa.String(length=20), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('apellido', sa.String(length=150), nullable=False),
        sa.Column('email', sa.String(length=250), nullable=False),
        sa.Column('nombreUsuario', sa.String(length=50), nullable=False),
        sa.Column('direccion', sa.String(length=250), nullable=True),
        sa.Column('altura', sa.String(length=10), nullable=False),
        sa.Column('departamento', sa.String(length=20), nullable=True),
        sa.Column('localidad', sa.String(length=150), nullable=False),
        sa.Column('ciudad', sa.String(length=150), nullable=False),
        sa.Column('estado', sa.String(length=15), nullable=False),
        sa.Column('urlFotoDocFrente', sa.String(length=500), nullable=False),
        sa.Column('urlFotoDocDorso', sa.String(length=500), nullable=False),
        sa.Column('fechaActualizacionFotoDni', sa.Date(), nullable=False),
        sa.Column('urlFotoPerfil', sa.String(length=500), nullable=True),
        sa.Column('hashContrasenia', sa.String(length=500), nullable=True),
        sa.PrimaryKeyConstraint('identificador'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('nombreUsuario')
    )
    op.create_table('seguros',
        sa.Column('nroPoliza', sa.String(length=30), nullable=False),
        sa.Column('compania', sa.String(length=150), nullable=False),
        sa.Column('polizaCombinada', sa.String(length=2), nullable=True),
        sa.Column('importe', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.PrimaryKeyConstraint('nroPoliza')
    )
    op.create_table('depositos',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('direccion', sa.String(length=350), nullable=False),
        sa.PrimaryKeyConstraint('identificador')
    )
    # sectores sin FK a empleados (circular, se agrega despues)
    op.create_table('sectores',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombreSector', sa.String(length=150), nullable=False),
        sa.Column('codigoSector', sa.String(length=10), nullable=True),
        sa.Column('responsableSector', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('identificador')
    )
    # empleados: FK a personas y sectores
    op.create_table('empleados',
        sa.Column('identificador', sa.Integer(), nullable=False),
        sa.Column('cargo', sa.String(length=100), nullable=True),
        sa.Column('sector', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['identificador'], ['personas.identificador']),
        sa.ForeignKeyConstraint(['sector'], ['sectores.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    # FK circular: sectores -> empleados
    op.create_foreign_key(
        'fk_sectores_empleados', 'sectores', 'empleados',
        ['responsableSector'], ['identificador']
    )
    # Tablas que dependen de personas/empleados
    op.create_table('subastadores',
        sa.Column('identificador', sa.Integer(), nullable=False),
        sa.Column('matricula', sa.String(length=15), nullable=True),
        sa.Column('region', sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(['identificador'], ['personas.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('clientes',
        sa.Column('identificador', sa.Integer(), nullable=False),
        sa.Column('numeroPais', sa.Integer(), nullable=True),
        sa.Column('admitido', sa.String(length=2), nullable=True),
        sa.Column('categoria', sa.String(length=10), nullable=True),
        sa.Column('verificador', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['identificador'], ['personas.identificador']),
        sa.ForeignKeyConstraint(['numeroPais'], ['paises.numero']),
        sa.ForeignKeyConstraint(['verificador'], ['empleados.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('duenios',
        sa.Column('identificador', sa.Integer(), nullable=False),
        sa.Column('numeroPais', sa.Integer(), nullable=True),
        sa.Column('verificacionFinanciera', sa.String(length=2), nullable=True),
        sa.Column('verificacionJudicial', sa.String(length=2), nullable=True),
        sa.Column('calificacionRiesgo', sa.Integer(), nullable=True),
        sa.Column('verificador', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['identificador'], ['personas.identificador']),
        sa.ForeignKeyConstraint(['numeroPais'], ['paises.numero']),
        sa.ForeignKeyConstraint(['verificador'], ['empleados.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('notificaciones',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('persona', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=30), nullable=False),
        sa.Column('leida', sa.String(length=2), nullable=False),
        sa.Column('creadaEn', sa.DateTime(timezone=True), nullable=False),
        sa.Column('detalle', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['persona'], ['personas.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('cuentasCobro',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('duenio', sa.Integer(), nullable=False),
        sa.Column('nombreBanco', sa.String(length=150), nullable=False),
        sa.Column('numeroCuenta', sa.String(length=50), nullable=False),
        sa.Column('pais', sa.Integer(), nullable=True),
        sa.Column('moneda', sa.String(length=3), nullable=False),
        sa.Column('activa', sa.String(length=2), nullable=False),
        sa.ForeignKeyConstraint(['duenio'], ['duenios.identificador']),
        sa.ForeignKeyConstraint(['pais'], ['paises.numero']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('mediosDePago',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cliente', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('verificado', sa.String(length=2), nullable=False),
        sa.Column('moneda', sa.String(length=3), nullable=False),
        sa.Column('activo', sa.String(length=2), nullable=False),
        sa.ForeignKeyConstraint(['cliente'], ['clientes.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('cuentasBancarias',
        sa.Column('medioPago', sa.Integer(), nullable=False),
        sa.Column('nombreBanco', sa.String(length=150), nullable=False),
        sa.Column('numeroCuenta', sa.String(length=50), nullable=False),
        sa.Column('pais', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['medioPago'], ['mediosDePago.identificador']),
        sa.ForeignKeyConstraint(['pais'], ['paises.numero']),
        sa.PrimaryKeyConstraint('medioPago')
    )
    op.create_table('tarjetasDeCredito',
        sa.Column('medioPago', sa.Integer(), nullable=False),
        sa.Column('ultimosCuatroDigitos', sa.String(length=4), nullable=False),
        sa.Column('nombreTitular', sa.String(length=150), nullable=False),
        sa.Column('fechaVencimiento', sa.Date(), nullable=False),
        sa.Column('red', sa.String(length=50), nullable=True),
        sa.Column('esInternacional', sa.String(length=2), nullable=False),
        sa.ForeignKeyConstraint(['medioPago'], ['mediosDePago.identificador']),
        sa.PrimaryKeyConstraint('medioPago')
    )
    op.create_table('chequesCertificados',
        sa.Column('medioPago', sa.Integer(), nullable=False),
        sa.Column('montoGarantizado', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('montoDisponible', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('fechaEntrega', sa.Date(), nullable=False),
        sa.Column('verificadoPor', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['medioPago'], ['mediosDePago.identificador']),
        sa.ForeignKeyConstraint(['verificadoPor'], ['empleados.identificador']),
        sa.PrimaryKeyConstraint('medioPago')
    )
    op.create_table('subastas',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(length=250), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=True),
        sa.Column('hora', sa.Time(), nullable=False),
        sa.Column('estado', sa.String(length=10), nullable=True),
        sa.Column('subastador', sa.Integer(), nullable=True),
        sa.Column('ubicacion', sa.String(length=350), nullable=True),
        sa.Column('capacidadAsistentes', sa.Integer(), nullable=True),
        sa.Column('tieneDeposito', sa.String(length=2), nullable=True),
        sa.Column('seguridadPropia', sa.String(length=2), nullable=True),
        sa.Column('categoria', sa.String(length=10), nullable=True),
        sa.Column('moneda', sa.String(length=3), nullable=False),
        sa.Column('duracionItemMinutos', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['subastador'], ['subastadores.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('productos',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fecha', sa.Date(), nullable=True),
        sa.Column('disponible', sa.String(length=2), nullable=True),
        sa.Column('descripcionCatalogo', sa.String(length=500), nullable=True),
        sa.Column('descripcionCompleta', sa.String(length=300), nullable=False),
        sa.Column('precioBase', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('revisor', sa.Integer(), nullable=False),
        sa.Column('duenio', sa.Integer(), nullable=False),
        sa.Column('seguro', sa.String(length=30), nullable=True),
        sa.Column('declaracionPropiedad', sa.Boolean(), nullable=False),
        sa.Column('fechaIngreso', sa.Date(), nullable=False),
        sa.Column('estadoProducto', sa.String(length=15), nullable=False),
        sa.Column('subastadorAsignado', sa.Integer(), nullable=True),
        sa.Column('deposito', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['deposito'], ['depositos.identificador']),
        sa.ForeignKeyConstraint(['duenio'], ['duenios.identificador']),
        sa.ForeignKeyConstraint(['revisor'], ['empleados.identificador']),
        sa.ForeignKeyConstraint(['seguro'], ['seguros.nroPoliza']),
        sa.ForeignKeyConstraint(['subastadorAsignado'], ['subastadores.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('fotos',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('producto', sa.Integer(), nullable=False),
        sa.Column('foto', sa.String(length=500), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['producto'], ['productos.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('detalleArtistico',
        sa.Column('producto', sa.Integer(), nullable=False),
        sa.Column('artista', sa.String(length=200), nullable=False),
        sa.Column('fechaObra', sa.Date(), nullable=True),
        sa.Column('historia', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['producto'], ['productos.identificador']),
        sa.PrimaryKeyConstraint('producto')
    )
    op.create_table('componentesProducto',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('producto', sa.Integer(), nullable=False),
        sa.Column('descripcion', sa.String(length=250), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['producto'], ['productos.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('asistentes',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('numeroPostor', sa.Integer(), nullable=False),
        sa.Column('cliente', sa.Integer(), nullable=False),
        sa.Column('subasta', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['cliente'], ['clientes.identificador']),
        sa.ForeignKeyConstraint(['subasta'], ['subastas.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('catalogos',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('descripcion', sa.String(length=250), nullable=False),
        sa.Column('subasta', sa.Integer(), nullable=True),
        sa.Column('responsable', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['responsable'], ['empleados.identificador']),
        sa.ForeignKeyConstraint(['subasta'], ['subastas.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('registroDeSubasta',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('subasta', sa.Integer(), nullable=False),
        sa.Column('duenio', sa.Integer(), nullable=False),
        sa.Column('producto', sa.Integer(), nullable=False),
        sa.Column('cliente', sa.Integer(), nullable=False),
        sa.Column('importe', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('comision', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('medioPago', sa.Integer(), nullable=True),
        sa.Column('costoEnvio', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('moneda', sa.String(length=3), nullable=False),
        sa.Column('retiraPersonalmente', sa.Boolean(), nullable=False),
        sa.Column('pagado', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['cliente'], ['clientes.identificador']),
        sa.ForeignKeyConstraint(['duenio'], ['duenios.identificador']),
        sa.ForeignKeyConstraint(['medioPago'], ['mediosDePago.identificador']),
        sa.ForeignKeyConstraint(['producto'], ['productos.identificador']),
        sa.ForeignKeyConstraint(['subasta'], ['subastas.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('itemsCatalogo',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('catalogo', sa.Integer(), nullable=False),
        sa.Column('producto', sa.Integer(), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.Column('precioBase', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('comision', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('subastado', sa.String(length=2), nullable=True),
        sa.Column('iniciadoEn', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalizadoEn', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['catalogo'], ['catalogos.identificador']),
        sa.ForeignKeyConstraint(['producto'], ['productos.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('pujos',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asistente', sa.Integer(), nullable=False),
        sa.Column('item', sa.Integer(), nullable=False),
        sa.Column('importe', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('ganador', sa.String(length=2), nullable=True),
        sa.Column('realizadaEn', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['asistente'], ['asistentes.identificador']),
        sa.ForeignKeyConstraint(['item'], ['itemsCatalogo.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )
    op.create_table('multas',
        sa.Column('identificador', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cliente', sa.Integer(), nullable=False),
        sa.Column('registroSubasta', sa.Integer(), nullable=False),
        sa.Column('importe', sa.Numeric(precision=18, scale=2), nullable=False),
        sa.Column('pagada', sa.String(length=2), nullable=False),
        sa.Column('fechaEmision', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fechaVencimiento', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['cliente'], ['clientes.identificador']),
        sa.ForeignKeyConstraint(['registroSubasta'], ['registroDeSubasta.identificador']),
        sa.PrimaryKeyConstraint('identificador')
    )


def downgrade() -> None:
    op.drop_table('multas')
    op.drop_table('pujos')
    op.drop_table('itemsCatalogo')
    op.drop_table('registroDeSubasta')
    op.drop_table('catalogos')
    op.drop_table('asistentes')
    op.drop_table('componentesProducto')
    op.drop_table('detalleArtistico')
    op.drop_table('fotos')
    op.drop_table('productos')
    op.drop_table('subastas')
    op.drop_table('chequesCertificados')
    op.drop_table('tarjetasDeCredito')
    op.drop_table('cuentasBancarias')
    op.drop_table('mediosDePago')
    op.drop_table('cuentasCobro')
    op.drop_table('notificaciones')
    op.drop_table('duenios')
    op.drop_table('clientes')
    op.drop_table('subastadores')
    op.drop_constraint('fk_sectores_empleados', 'sectores', type_='foreignkey')
    op.drop_table('empleados')
    op.drop_table('sectores')
    op.drop_table('depositos')
    op.drop_table('seguros')
    op.drop_table('personas')
    op.drop_table('paises')
