CREATE TABLE paises (
    numero          INT             NOT NULL,
    nombre          VARCHAR(250)    NOT NULL,
    nombreCorto     VARCHAR(250)    NULL,
    capital         VARCHAR(250)    NOT NULL,
    nacionalidad    VARCHAR(250)    NOT NULL,
    idiomas         VARCHAR(150)    NOT NULL,
    CONSTRAINT pk_paises PRIMARY KEY (numero)
);

CREATE TABLE personas (
    identificador   SERIAL          NOT NULL,
    documento       VARCHAR(20)     NOT NULL,
    nombre          VARCHAR(150)    NOT NULL,
    direccion       VARCHAR(250)    NULL,
    estado          VARCHAR(15)     NOT NULL DEFAULT 'pendiente'
                    CONSTRAINT chkEstado CHECK (estado IN ('pendiente', 'activo', 'inactivo')),
    foto            BYTEA           NULL,
    -- Columnas agregadas
    apellido                  VARCHAR(150)    NOT NULL,
    email                     VARCHAR(250)    NOT NULL UNIQUE,
    nombreUsuario             VARCHAR(50)     NOT NULL UNIQUE,
    altura                    VARCHAR(10)     NOT NULL,
    departamento              VARCHAR(20)     NULL,
    localidad                 VARCHAR(150)    NOT NULL,
    ciudad                    VARCHAR(150)    NOT NULL,
    urlFotoDocFrente          VARCHAR(500)    NOT NULL,
    urlFotoDocDorso           VARCHAR(500)    NOT NULL,
    fechaActualizacionFotoDni DATE            NOT NULL DEFAULT CURRENT_DATE,
    urlFotoPerfil             VARCHAR(500)    NULL,
    hashContrasenia           VARCHAR(500)    NULL,
    CONSTRAINT pk_personas PRIMARY KEY (identificador)
);

CREATE TABLE empleados (
    identificador   INT             NOT NULL,
    cargo           VARCHAR(100)    NULL,
    sector          INT             NULL,
    CONSTRAINT pk_empleados PRIMARY KEY (identificador)
);

-- Dependencia circular con empleados resuelta con ALTER TABLE.
CREATE TABLE sectores (
    identificador       SERIAL          NOT NULL,
    nombreSector        VARCHAR(150)    NOT NULL,
    codigoSector        VARCHAR(10)     NULL,
    responsableSector   INT             NULL,
    CONSTRAINT pk_sectores PRIMARY KEY (identificador)
);

ALTER TABLE empleados
    ADD CONSTRAINT fk_empleados_sectores
    FOREIGN KEY (sector) REFERENCES sectores (identificador);

ALTER TABLE sectores
    ADD CONSTRAINT fk_sectores_empleados
    FOREIGN KEY (responsableSector) REFERENCES empleados (identificador);

ALTER TABLE empleados
    ADD CONSTRAINT fk_empleados_personas
    FOREIGN KEY (identificador) REFERENCES personas (identificador);

CREATE TABLE seguros (
    nroPoliza           VARCHAR(30)     NOT NULL,
    compania            VARCHAR(150)    NOT NULL,
    polizaCombinada     VARCHAR(2)      NULL
                        CONSTRAINT chkPolizaCombinada CHECK (polizaCombinada IN ('si', 'no')),
    importe             DECIMAL(18,2)   NOT NULL
                        CONSTRAINT chkImporte CHECK (importe > 0),
    CONSTRAINT pk_seguros PRIMARY KEY (nroPoliza)
);

CREATE TABLE clientes (
    identificador   INT             NOT NULL,
    numeroPais      INT             NULL,
    admitido        VARCHAR(2)      NULL
                    CONSTRAINT chkAdmitido CHECK (admitido IN ('si', 'no')),
    categoria       VARCHAR(10)     NULL
                    CONSTRAINT chkCategoria CHECK (categoria IN ('comun', 'especial', 'plata', 'oro', 'platino')),
    verificador     INT             NOT NULL,
    CONSTRAINT pk_clientes PRIMARY KEY (identificador),
    CONSTRAINT fk_clientes_personas  FOREIGN KEY (identificador) REFERENCES personas (identificador),
    CONSTRAINT fk_clientes_empleados FOREIGN KEY (verificador)   REFERENCES empleados (identificador),
    CONSTRAINT fk_clientes_paises    FOREIGN KEY (numeroPais)    REFERENCES paises (numero)
);

CREATE TABLE duenios (
    identificador           INT             NOT NULL,
    numeroPais              INT             NULL,
    verificacionFinanciera  VARCHAR(2)      NULL
                            CONSTRAINT chkVF CHECK (verificacionFinanciera IN ('si', 'no')),
    verificacionJudicial    VARCHAR(2)      NULL
                            CONSTRAINT chkVJ CHECK (verificacionJudicial IN ('si', 'no')),
    calificacionRiesgo      INT             NULL
                            CONSTRAINT chkCR CHECK (calificacionRiesgo IN (1, 2, 3, 4, 5, 6)),
    verificador             INT             NOT NULL,
    CONSTRAINT pk_duenios PRIMARY KEY (identificador),
    CONSTRAINT fk_duenios_personas  FOREIGN KEY (identificador) REFERENCES personas (identificador),
    CONSTRAINT fk_duenios_empleados FOREIGN KEY (verificador)   REFERENCES empleados (identificador)
);

CREATE TABLE subastadores (
    identificador   INT             NOT NULL,
    matricula       VARCHAR(15)     NULL,
    region          VARCHAR(50)     NULL,
    CONSTRAINT pk_subastadores PRIMARY KEY (identificador),
    CONSTRAINT fk_subastadores_personas FOREIGN KEY (identificador) REFERENCES personas (identificador)
);

CREATE TABLE subastas (
    identificador       SERIAL          NOT NULL,
    nombre              VARCHAR(250)    NOT NULL,
    fecha               DATE            NULL
                        CONSTRAINT chkFecha CHECK (fecha > CURRENT_DATE + INTERVAL '10 days'),
    hora                TIME            NOT NULL,
    estado              VARCHAR(10)     NULL
                        CONSTRAINT chkES CHECK (estado IN ('programada', 'abierta', 'cerrada')),
    subastador          INT             NULL,
    ubicacion           VARCHAR(350)    NULL,
    capacidadAsistentes INT             NULL,
    tieneDeposito       VARCHAR(2)      NULL
                        CONSTRAINT chkTD CHECK (tieneDeposito IN ('si', 'no')),
    seguridadPropia     VARCHAR(2)      NULL
                        CONSTRAINT chkSP CHECK (seguridadPropia IN ('si', 'no')),
    categoria           VARCHAR(10)     NULL
                        CONSTRAINT chkCS CHECK (categoria IN ('comun', 'especial', 'plata', 'oro', 'platino')),
    -- Columnas agregadas
    moneda              VARCHAR(3)      NOT NULL
                        CONSTRAINT chkMoneda CHECK (moneda IN ('ARS', 'USD')),
    duracionItemMinutos INT             NOT NULL
                        CONSTRAINT chkDuracion CHECK (duracionItemMinutos > 0),
    CONSTRAINT pk_subastas PRIMARY KEY (identificador),
    CONSTRAINT fk_subastas_subastadores FOREIGN KEY (subastador) REFERENCES subastadores (identificador)
);

CREATE TABLE depositos (
    identificador   SERIAL          NOT NULL,
    nombre          VARCHAR(150)    NOT NULL,
    direccion       VARCHAR(350)    NOT NULL,
    CONSTRAINT pk_depositos PRIMARY KEY (identificador)
);

CREATE TABLE productos (
    identificador           SERIAL          NOT NULL,
    fecha                   DATE            NULL,
    disponible              VARCHAR(2)      NULL
                            CONSTRAINT chkD CHECK (disponible IN ('si', 'no')),
    descripcionCatalogo     VARCHAR(500)    NULL DEFAULT 'No Posee',
    descripcionCompleta     VARCHAR(300)    NOT NULL,
    precioBase              DECIMAL(18,2)   NOT NULL CONSTRAINT chkPrecioBase CHECK (precioBase > 0),
    revisor                 INT             NOT NULL,
    duenio                  INT             NOT NULL,
    seguro                  VARCHAR(30)     NULL,
    -- Columnas agregadas
    declaracionPropiedad    BOOLEAN         NOT NULL DEFAULT FALSE,
    fechaIngreso            DATE            NOT NULL DEFAULT CURRENT_DATE,
    -- Estado del ciclo de vida del producto dentro del sistema de subastas.
    -- pendiente:             recien creado, esperando verificacion automatica.
    -- asignado:              verificacion aprobada, en el pool de un subastador.
    -- rechazado:             verificacion no aprobada.
    -- pendiente_confirmacion: agregado a un catalogo con precio y comision, esperando confirmacion del dueño.
    --                         Si el dueño rechaza las condiciones, vuelve a "asignado".
    -- en_subasta:            dueño acepto condiciones, siendo subastado.
    -- vendido:               subastado y vendido exitosamente.
    estadoProducto          VARCHAR(15)     NOT NULL DEFAULT 'pendiente'
                            CONSTRAINT chkEstadoProducto CHECK (estadoProducto IN ('pendiente', 'asignado', 'rechazado', 'pendiente_confirmacion', 'en_subasta', 'vendido')),
    subastadorAsignado      INT             NULL,
    -- Deposito donde se encuentra el producto una vez aceptado.
    -- NULL mientras el producto no haya sido recibido fisicamente.
    deposito                INT             NULL,
    CONSTRAINT pk_productos PRIMARY KEY (identificador),
    CONSTRAINT fk_productos_empleados    FOREIGN KEY (revisor)            REFERENCES empleados (identificador),
    CONSTRAINT fk_productos_duenios      FOREIGN KEY (duenio)             REFERENCES duenios (identificador),
    CONSTRAINT fk_productos_subastadores FOREIGN KEY (subastadorAsignado) REFERENCES subastadores (identificador),
    CONSTRAINT fk_productos_depositos    FOREIGN KEY (deposito)           REFERENCES depositos (identificador)
);

CREATE TABLE fotos (
    identificador   SERIAL  NOT NULL,
    producto        INT     NOT NULL,
    foto            BYTEA   NOT NULL,
    -- Orden de visualizacion en la ficha del producto.
    orden           INT     NOT NULL DEFAULT 1,
    CONSTRAINT pk_fotos PRIMARY KEY (identificador),
    CONSTRAINT fk_fotos_productos FOREIGN KEY (producto) REFERENCES productos (identificador)
);

CREATE TABLE catalogos (
    identificador   SERIAL          NOT NULL,
    descripcion     VARCHAR(250)    NOT NULL,
    subasta         INT             NULL,
    responsable     INT             NOT NULL,
    CONSTRAINT pk_catalogos PRIMARY KEY (identificador),
    CONSTRAINT fk_catalogos_empleados FOREIGN KEY (responsable) REFERENCES empleados (identificador),
    CONSTRAINT fk_catalogos_subastas  FOREIGN KEY (subasta)     REFERENCES subastas (identificador)
);

CREATE TABLE itemsCatalogo (
    identificador   SERIAL          NOT NULL,
    catalogo        INT             NOT NULL,
    producto        INT             NOT NULL,
    -- Orden en que el item se subasta dentro del catalogo.
    orden           INT             NOT NULL DEFAULT 1,
    -- Legacy: el precio base real vive en productos.precioBase.
    -- Se mantiene porque no se puede cambiar con el esquema original :(
    precioBase      DECIMAL(18,2)   NOT NULL CONSTRAINT chkPB CHECK (precioBase > 0.01),
    comision        DECIMAL(18,2)   NOT NULL CONSTRAINT chkC  CHECK (comision > 0.01),
    subastado       VARCHAR(2)      NULL
                    CONSTRAINT chkS CHECK (subastado IN ('si', 'no')),
    -- Momento en que empieza el turno de este item. Necesario para el timer!!!
    iniciadoEn      TIMESTAMPTZ     NULL,
    finalizadoEn    TIMESTAMPTZ     NULL,
    CONSTRAINT pk_itemsCatalogo PRIMARY KEY (identificador),
    CONSTRAINT fk_itemsCatalogo_catalogos FOREIGN KEY (catalogo) REFERENCES catalogos (identificador),
    CONSTRAINT fk_itemsCatalogo_productos FOREIGN KEY (producto)  REFERENCES productos (identificador)
);

CREATE TABLE asistentes (
    identificador   SERIAL  NOT NULL,
    numeroPostor    INT     NOT NULL,
    cliente         INT     NOT NULL,
    subasta         INT     NOT NULL,
    CONSTRAINT pk_asistentes PRIMARY KEY (identificador),
    CONSTRAINT fk_asistentes_clientes FOREIGN KEY (cliente) REFERENCES clientes (identificador),
    CONSTRAINT fk_asistentes_subastas FOREIGN KEY (subasta) REFERENCES subastas (identificador)
);

CREATE TABLE pujos (
    identificador   SERIAL          NOT NULL,
    asistente       INT             NOT NULL,
    item            INT             NOT NULL,
    importe         DECIMAL(18,2)   NOT NULL CONSTRAINT chkI CHECK (importe > 0.01),
    ganador         VARCHAR(2)      NULL DEFAULT 'no'
                    CONSTRAINT chkG CHECK (ganador IN ('si', 'no')),
    -- Momento exacto en que se registro el pujo. Necesario para ordenar pujos correctamente!!
    realizadaEn     TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_pujos PRIMARY KEY (identificador),
    CONSTRAINT fk_pujos_asistentes   FOREIGN KEY (asistente) REFERENCES asistentes (identificador),
    CONSTRAINT fk_pujos_itemsCatalogo FOREIGN KEY (item)     REFERENCES itemsCatalogo (identificador)
);

CREATE TABLE registroDeSubasta (
    identificador   SERIAL          NOT NULL,
    subasta         INT             NOT NULL,
    duenio          INT             NOT NULL,
    producto        INT             NOT NULL,
    cliente         INT             NOT NULL,
    importe         DECIMAL(18,2)   NOT NULL CONSTRAINT chkImportePagado   CHECK (importe > 0.01),
    comision        DECIMAL(18,2)   NOT NULL CONSTRAINT chkComisionPagada  CHECK (comision > 0.01),
    -- Columnas agregadas
    medioPago           INT             NULL,
    costoEnvio          DECIMAL(18,2)   NOT NULL DEFAULT 0,
    moneda              VARCHAR(3)      NOT NULL
                        CONSTRAINT chkMonedaRegistro CHECK (moneda IN ('ARS', 'USD')),
    retiraPersonalmente BOOLEAN         NOT NULL DEFAULT FALSE,
    pagado              BOOLEAN         NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_registroDeSubasta PRIMARY KEY (identificador),
    CONSTRAINT fk_registroDeSubasta_subastas  FOREIGN KEY (subasta)  REFERENCES subastas (identificador),
    CONSTRAINT fk_registroDeSubasta_duenios   FOREIGN KEY (duenio)   REFERENCES duenios (identificador),
    CONSTRAINT fk_registroDeSubasta_producto  FOREIGN KEY (producto)  REFERENCES productos (identificador),
    CONSTRAINT fk_registroDeSubasta_clientes  FOREIGN KEY (cliente)  REFERENCES clientes (identificador)
);

CREATE TABLE mediosDePago (
    identificador   SERIAL          NOT NULL,
    cliente         INT             NOT NULL,
    tipo            VARCHAR(20)     NOT NULL
                    CONSTRAINT chkTipoMedio CHECK (tipo IN ('cuentaBancaria', 'tarjetaCredito', 'chequeCertificado')),
    verificado      VARCHAR(2)      NOT NULL DEFAULT 'no'
                    CONSTRAINT chkVerificado CHECK (verificado IN ('si', 'no')),
    moneda          VARCHAR(3)      NOT NULL DEFAULT 'ARS'
                    CONSTRAINT chkMonedaMedio CHECK (moneda IN ('ARS', 'USD')),
    activo          VARCHAR(2)      NOT NULL DEFAULT 'si'
                    CONSTRAINT chkActivoMedio CHECK (activo IN ('si', 'no')),
    CONSTRAINT pk_mediosDePago PRIMARY KEY (identificador),
    CONSTRAINT fk_mediosDePago_clientes FOREIGN KEY (cliente) REFERENCES clientes (identificador)
);

ALTER TABLE registroDeSubasta
    ADD CONSTRAINT fk_registroDeSubasta_mediosPago
    FOREIGN KEY (medioPago) REFERENCES mediosDePago (identificador);

CREATE TABLE cuentasBancarias (
    medioPago       INT             NOT NULL,
    nombreBanco     VARCHAR(150)    NOT NULL,
    numeroCuenta    VARCHAR(50)     NOT NULL,
    pais            INT             NULL,
    CONSTRAINT pk_cuentasBancarias PRIMARY KEY (medioPago),
    CONSTRAINT fk_cuentasBancarias_medios  FOREIGN KEY (medioPago) REFERENCES mediosDePago (identificador),
    CONSTRAINT fk_cuentasBancarias_paises  FOREIGN KEY (pais)      REFERENCES paises (numero)
);

CREATE TABLE tarjetasDeCredito (
    medioPago               INT             NOT NULL,
    ultimosCuatroDigitos    VARCHAR(4)      NOT NULL,
    nombreTitular           VARCHAR(150)    NOT NULL,
    fechaVencimiento        DATE            NOT NULL,
    red                     VARCHAR(50)     NULL,
    esInternacional         VARCHAR(2)      NOT NULL DEFAULT 'no'
                            CONSTRAINT chkEsInternacional CHECK (esInternacional IN ('si', 'no')),
    CONSTRAINT pk_tarjetasDeCredito PRIMARY KEY (medioPago),
    CONSTRAINT fk_tarjetasDeCredito_medios FOREIGN KEY (medioPago) REFERENCES mediosDePago (identificador)
);

CREATE TABLE chequesCertificados (
    medioPago           INT             NOT NULL,
    montoGarantizado    DECIMAL(18,2)   NOT NULL CONSTRAINT chkMontoGarantizado CHECK (montoGarantizado > 0),
    montoDisponible     DECIMAL(18,2)   NOT NULL CONSTRAINT chkMontoDisponible  CHECK (montoDisponible >= 0),
    fechaEntrega        DATE            NOT NULL,
    verificadoPor       INT             NULL,
    CONSTRAINT pk_chequesCertificados PRIMARY KEY (medioPago),
    CONSTRAINT fk_chequesCertificados_medios    FOREIGN KEY (medioPago)     REFERENCES mediosDePago (identificador),
    CONSTRAINT fk_chequesCertificados_empleados FOREIGN KEY (verificadoPor) REFERENCES empleados (identificador)
);

CREATE TABLE detalleArtistico (
    producto    INT             NOT NULL,
    artista     VARCHAR(200)    NOT NULL,
    fechaObra   DATE            NULL,
    historia    TEXT            NULL,
    CONSTRAINT pk_detalleArtistico PRIMARY KEY (producto),
    CONSTRAINT fk_detalleArtistico_productos FOREIGN KEY (producto) REFERENCES productos (identificador)
);

CREATE TABLE componentesProducto (
    identificador   SERIAL          NOT NULL,
    producto        INT             NOT NULL,
    descripcion     VARCHAR(250)    NOT NULL,
    cantidad        INT             NOT NULL DEFAULT 1,
    CONSTRAINT pk_componentesProducto PRIMARY KEY (identificador),
    CONSTRAINT fk_componentesProducto_productos FOREIGN KEY (producto) REFERENCES productos (identificador)
);

CREATE TABLE cuentasCobro (
    identificador   SERIAL          NOT NULL,
    duenio          INT             NOT NULL,
    nombreBanco     VARCHAR(150)    NOT NULL,
    numeroCuenta    VARCHAR(50)     NOT NULL,
    pais            INT             NULL,
    moneda          VARCHAR(3)      NOT NULL
                    CONSTRAINT chkMonedaCobro CHECK (moneda IN ('ARS', 'USD')),
    activa          VARCHAR(2)      NOT NULL DEFAULT 'si'
                    CONSTRAINT chkActivaCobro CHECK (activa IN ('si', 'no')),
    CONSTRAINT pk_cuentasCobro PRIMARY KEY (identificador),
    CONSTRAINT fk_cuentasCobro_duenios FOREIGN KEY (duenio) REFERENCES duenios (identificador),
    CONSTRAINT fk_cuentasCobro_paises  FOREIGN KEY (pais)   REFERENCES paises (numero)
);

CREATE TABLE notificaciones (
    identificador   SERIAL          NOT NULL,
    persona         INT             NOT NULL,
    tipo            VARCHAR(30)     NOT NULL
                    CONSTRAINT chkTipoNotif CHECK (tipo IN (
                        'compra_ganada',
                        'producto_vendido',
                        'producto_rechazado',
                        'producto_aceptado',
                        'devolucion_producto'
                    )),
    leida           VARCHAR(2)      NOT NULL DEFAULT 'no'
                    CONSTRAINT chkLeida CHECK (leida IN ('si', 'no')),
    creadaEn        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    detalle         TEXT            NOT NULL DEFAULT '{}',
    CONSTRAINT pk_notificaciones PRIMARY KEY (identificador),
    CONSTRAINT fk_notificaciones_personas FOREIGN KEY (persona) REFERENCES personas (identificador)
);

CREATE TABLE multas (
    identificador       SERIAL          NOT NULL,
    cliente             INT             NOT NULL,
    registroSubasta     INT             NOT NULL,
    importe             DECIMAL(18,2)   NOT NULL CONSTRAINT chkImporteMulta CHECK (importe > 0),
    pagada              VARCHAR(2)      NOT NULL DEFAULT 'no'
                        CONSTRAINT chkPagada CHECK (pagada IN ('si', 'no')),
    fechaEmision        TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    fechaVencimiento    TIMESTAMPTZ     NOT NULL,
    CONSTRAINT pk_multas PRIMARY KEY (identificador),
    CONSTRAINT fk_multas_clientes          FOREIGN KEY (cliente)         REFERENCES clientes (identificador),
    CONSTRAINT fk_multas_registroSubasta   FOREIGN KEY (registroSubasta) REFERENCES registroDeSubasta (identificador)
);

-- ============================================================
-- DATOS INICIALES
-- ============================================================

-- Usuario especial que representa a la empresa en el sistema.
-- Se usa como cliente en registroDeSubasta cuando ningun cliente
-- puja por un articulo y la empresa lo compra al precio base.
-- El ID 1 esta reservado para este usuario especial.
-- Hay que crearlo antes de cualquier otro dato en personas y clientes!!!!!
-- Al final de este archivo ya están los INSERT :)

INSERT INTO personas (
    identificador, documento, nombre, apellido, email, nombreUsuario,
    direccion, altura, localidad, ciudad,
    urlFotoDocFrente, urlFotoDocDorso, fechaActualizacionFotoDni,
    estado, hashContrasenia
)
VALUES (
    1, '00000000', 'Midnight', 'Lace', 'contacto@midnightlace.com', 'midnight_lace',
    'Alsina', '451', 'CABA', 'CABA',
    'n/a', 'n/a', CURRENT_DATE,
    'activo', 'n/a'
);

INSERT INTO empleados (identificador, cargo, sector)
VALUES (1, 'Midnight Lace', NULL);

INSERT INTO clientes (identificador, admitido, categoria, verificador)
VALUES (1, 'si', 'platino', 1);
