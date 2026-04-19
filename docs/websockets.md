# Tiempo real — Eventos WebSocket

## Prefacio

El `swagger.yaml` describe la interfaz REST. La subasta requiere comunicación servidor -> cliente en tiempo real que REST no cubre: el servidor necesita notificar a todos los compradores conectados cuando alguien puja, cuando cambia el ítem o cuando finaliza la subasta, sin que cada cliente tenga que hacer hacer peticiones constantemente. Para esto se usa WebSockets.

---

## Conexión a una subasta

```
wss://<URL>/v1/ws/subastas/{idSubasta}
```

El JWT se envía en el header del handshake:

```
Authorization: Bearer <token>
```

El backend valida el token antes de aceptar la conexión. Cualquier comprador registrado puede conectarse a cualquier subasta para seguirla. Sin embargo, si la categoría de la subasta supera la del comprador, la conexión se acepta pero el cliente no puede pujar. Si el cliente intenta pujar sin cumplir la categoría, recibe el evento `errorPuja` con código `CATEGORIA_INSUFICIENTE`.

Un usuario puede estar conectado a múltiples subastas simultáneamente. Cada conexión es independiente y tiene su propia sesión WS.

### Reconexión

Si el usuario cierra la app o pierde conectividad, la conexión WS se cierra con código `1001`. Al reconectarse, el backend detecta que ya existe un registro en `asistentes` para ese cliente en esa subasta y no crea uno nuevo — el `numeroPostor` original se mantiene. El backend emite `asistenciaConfirmada` con el número original. El frontend debe llamar mediante HTTP a `GET /subastas/{id}/item-actual` para sincronizar el estado actual sin esperar el próximo evento WS.

### Asistencia registrada

Al aceptar la conexión, el backend registra automáticamente al cliente como asistente de la subasta en la tabla `asistentes`:

1. Verifica si ya existe un registro para ese cliente en esa subasta (ver Reconexión).

2. Si no existe, calcula el próximo `numeroPostor` (`MAX(numeroPostor) + 1` para esa subasta) y hace el INSERT.

3. El `identificador` resultante queda asociado a la sesión WS del cliente y se usa internamente para registrar sus pujas en la tabla `pujos`.

El `numeroPostor` es independiente y secuencial por subasta — el primero en conectarse es el postor 1, el segundo el 2, etc. Es análogo al número que se entrega en un remate presencial.

El backend emite el evento `asistenciaConfirmada` al cliente como confirmación:

```json
{
    "evento": "asistenciaConfirmada",
    "datos": {
        "numeroPostor": 7,
        "idSubasta": 5
    }
}
```

---

## Unidireccionalidad

El WebSocket es **unidireccional** en cuanto a lógica de negocio: el servidor emite eventos que le llegan al cliente.

Las pujas **no se realizan por WebSocket**. Se realizan mediante HTTP:

```
POST /subastas/{idSubasta}/items/{idItem}/pujas
```

Una vez que el backend confirma la puja, emite el evento `nuevaPuja` a todos los clientes conectados a esa subasta.

---

## Eventos que emite el servidor → cliente

### `nuevaPuja`

Se emite a todos los conectados cada vez que se registra una puja válida.

```json
{
    "evento": "nuevaPuja",
    "datos": {
        "idItem": 42,
        "importe": 15150.0,
        "pujaMinima": 15251.0,
        "pujaMaxima": 17150.0
    }
}
```

| Campo        | Tipo           | Descripción                                                                           |
| ------------ | -------------- | ------------------------------------------------------------------------------------- |
| `idItem`     | integer        | Ítem sobre el que se realizó la puja                                                  |
| `importe`    | number         | Importe de la nueva mejor oferta                                                      |
| `pujaMinima` | number         | Mínimo válido para la próxima puja (última oferta + 1% del precio base)               |
| `pujaMaxima` | number \| null | Máximo válido (última oferta + 20% del precio base). `null` para subastas oro/platino |

---

### `cambioItem`

Se emite cuando expira el tiempo asignado a un ítem (`duracionItemMinutos`) y el
backend avanza al siguiente.

```json
{
    "evento": "cambioItem",
    "datos": {
        "itemAnterior": {
            "idItem": 42,
            "vendido": false
        },
        "itemActual": {
            "idItem": 43,
            "descripcionProducto": "Vestido Osaki Nana 2008",
            "precioBase": 8000.0,
            "finalizaEn": "2026-09-01T15:30:00Z"
        }
    }
}
```

| Campo                            | Tipo                         | Descripción                                                             |
| -------------------------------- | ---------------------------- | ----------------------------------------------------------------------- |
| `itemAnterior.idItem`            | integer                      | Ítem que acaba de finalizar                                             |
| `itemAnterior.vendido`           | boolean                      | `true` si hubo al menos una puja ganadora                               |
| `itemActual.idItem`              | integer                      | Ítem que comienza ahora                                                 |
| `itemActual.descripcionProducto` | string                       | Descripción breve para mostrar en pantalla                              |
| `itemActual.precioBase`          | number                       | Precio base del nuevo ítem                                              |
| `itemActual.finalizaEn`          | string (ISO 8601 con offset) | Momento exacto en que expira el turno del ítem. Usar para el countdown. |

---

### `pujaGanadora`

Se emite junto con `cambioItem` cuando el ítem que finalizó tenía al menos una puja.
Identifica al ganador para que el frontend pueda mostrarlo.

```json
{
    "evento": "pujaGanadora",
    "datos": {
        "idItem": 42,
        "idCliente": 7,
        "importe": 15150.0
    }
}
```

| Campo       | Tipo    | Descripción               |
| ----------- | ------- | ------------------------- |
| `idItem`    | integer | Ítem vendido              |
| `idCliente` | integer | ID del comprador ganador  |
| `importe`   | number  | Importe final de la venta |

---

### `subastaFinalizada`

Se emite cuando el último ítem del catálogo termina su turno. El frontend debe
redirigir al comprador fuera de la sala de subasta.

```json
{
    "evento": "subastaFinalizada",
    "datos": {
        "idSubasta": 5
    }
}
```

---

## Resumen de eventos servidor → cliente

| Evento                 | Cuándo se emite                           | Destinatario                      |
| ---------------------- | ----------------------------------------- | --------------------------------- |
| `asistenciaConfirmada` | Al aceptar la conexión WS                 | Solo el cliente que se conectó    |
| `nuevaPuja`            | Al registrarse una puja válida            | Todos los conectados a la subasta |
| `cambioItem`           | Al expirar el turno de un ítem            | Todos los conectados a la subasta |
| `pujaGanadora`         | Al expirar el turno con al menos una puja | Todos los conectados a la subasta |
| `subastaFinalizada`    | Al terminar el último ítem                | Todos los conectados a la subasta |

---

## Códigos de cierre de conexión

| Código | Significado                                |
| ------ | ------------------------------------------ |
| `1000` | Cierre normal (subasta finalizada)         |
| `1001` | Cliente cerró la app o perdió conectividad |
| `4001` | Token inválido o expirado                  |
| `4003` | Usuario suspendido (multa impaga)          |
| `4004` | Subasta no encontrada                      |
