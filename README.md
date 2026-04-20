# Midnight Lace

Una obra del **Grupo 1**:

- Abeledo, Federico
- Ghillino, Rocío Belén
- Novello, Victoria Abril
- Romero, Mailén Belén

---

## Prefacio

Creamos _Midnight Lace_ con la consigna de que teniamos que desarrollar una aplicación para una casa de subastas. Sin saber mucho del tema decidimos darle personalidad a la aplicación, centrándonos en la compra/venta de vestidos EGL (_Elegant Gothic Lolita_) y basando toda la estética y diseño en eso.

Como comentaba anteriormente, la app permite tanto la venta, como la compra y seguimiento en tiempo real de las subastas.

---

## Android Studio

La primera entrega tiene una consigna opcional que dice de hacer alguna pantalla en Android Studio.

Si bien desde el grupo decidimos que vamos a hacer el frontend con React Native, vamos a hacer la pantalla splash, login, home y todas las subastas en Android Studio solamente como una demo en la primera entrega.

Para que Android Studio reconozca el proyecto fácilmente se recomienda abrir el misml desde la carpeta `android-studio`, no desde la raíz de este repositorio.

En el inicio de sesión definimos un usuario de prueba:

- **Correo**: puede estar vacío o ser cualquier cadena, se ignora en esta demo.
- **Contraseña:** `123`

---

## Stack

- **Frontend:** habrá una pequeña demostración hecha en Android Studio para esta primera entrega, después se hará en **React Native**. En esta primera entrega tenemos hechos los prototipos que fueron hechos en **Figma**.
- **Backend:** por definir. La API REST documentada en **Swagger**, en el archivo `swagger.yaml`. También hay un archivo `websockets.md`, donde se detallan los eventos WebSockets que tendrá la app, ya que en Swagger no se pueden documentar estos.
- **Base de datos:** La estructura original se mantiene, solamente que fue traducida a la sintaxis de **PostgreSQL**, que es el motor que vamos a usar. También se agregaron muchos campos necesarios.

---

## Decisiones relevantes

### Registro

El registro de un comprador pasa por estados bien definidos en `personas.estado`:

| Estado      | Significado                                                       |
| ----------- | ----------------------------------------------------------------- |
| `pendiente` | El usuario está en etapa de verificación o no seteó la contraseña |
| `activo`    | Aceptado en la verificación y con contraseña                      |
| `inactivo`  | Rechazado o dado de baja                                          |

Esto se complementa con `clientes.admitido` (`si`/`no`) y `clientes.categoria`. La combinación de ambos campos permite distinguir sin ambigüedad cada momento del flujo: usuario en verificación, rechazado, aceptado esperando que setee contraseña o activo.

### Pool del subastador

Cuando un artículo es creado por un dueño, el mismo pasa por una verificación y, si se acepta, se le asigna a un subastador.

El subastador cuando quiere crear una nueva subasta puede elegir entre una lista de articulos que le fueron asignados. En el equipo a esta lista le dimos el nombre de _pool del subastador_ a fines de no confundirlo con el catálogo de la subasta.

### Ciclo de vida de un producto

Los artículos que los dueños ofrecen para subastar siguen un ciclo de vida definido en `productos.estadoProducto`:

`pendiente` → `asignado` → `pendiente_confirmacion` → `en_subasta` → `vendido`

- El precio base lo fija el dueño al cargar el artículo, no el subastador.
- Cuando el subastador agrega el artículo a un catálogo, define la **comisión** y el dueño recibe una notificación para aceptar o rechazar las condiciones. Si rechaza, el artículo vuelve a `asignado`.
- `rechazado` es un estado terminal que aplica solo cuando la verificación automática falla.

Entonces, los posibles estados son:
| Estado | Significado |
|---|---|
| `pendiente` | Recién creado, esperando verificación automática |
| `asignado` | Verificación aprobada, en el pool del subastador |
| `rechazado` | Verificación no aprobada |
| `pendiente_confirmacion` | Agregado a un catalogo con precio y comision, esperando confirmacion del dueño. Si el dueño rechaza las condiciones, vuelve a "asignado" |
| `en_subasta` | Dueño acepto condiciones, siendo subastado |
| `vendido` | Subastado y vendido exitosamente |

### Pujas — WebSockets y HTTP

Las subastas son dinámicas ascendentes. Las pujas se comunican por WebSockets, todos los conectados a una subasta reciben en tiempo real cada nueva oferta. Esto permite la comunicación servidor -> cliente, sin que el cliente tenga que pedirlo.

La puja en sí sí va por HTTP para garantizar consistencia y evitar que se pisen.

### Roles

Los únicos dos roles que pueden convivir en un mismo usuario son `comprador` y `duenio`, de hecho un `duenio` empieza su cuenta sí o sí siendo primero `comprador` (esto no quiere decir que está obligado a comprar algo antes de publicar).

Después hay dos tipos de usuarios más `subastador` y `empleado`. Los nombres son autoexplicativos, pero me tomo el atrevimiento de aclarar que los usuarios `empleado` vendrían a ser los administradores.

---

## Estructura

```text
.
├── android-studio/          # Proyecto Android Studio (solo para la primera entrega)
├── docs/                    # Documentación y diseño
│   ├── prototipos/          # Assets de diseño y prototipado
│   │   ├── png/             # Pantallas en PNG
│   │   ├── svg/             # Pantallas en SVG
│   │   └── logo.svg         # Logo de Midnight Lace
│   ├── schema_postgres.sql  # Esquema de la DB
│   ├── swagger.yaml         # Documentación de la API REST
│   └── websockets.md        # Documentación de eventos WS
└── README.md                # Lo que estás leyendo...
```
