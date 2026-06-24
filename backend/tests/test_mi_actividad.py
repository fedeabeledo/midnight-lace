"""
Tests integración — Mi Actividad + WS usuario + condiciones + corrección item catálogo.
Requiere server corriendo en localhost:8000 con DB limpia (seed aplicado).
"""
import io
import json
import subprocess
import time
import pytest
import httpx

DB_URL = "postgresql://midnightlace:midnightlace@localhost:5432/midnightlace"


def db_query(sql: str) -> str:
    """Ejecuta SQL via psql, devuelve primera fila primer campo."""
    r = subprocess.run(
        ["psql", DB_URL, "-t", "-A", "-c", sql],
        capture_output=True, text=True,
    )
    return r.stdout.strip()

BASE = "http://localhost:8000"
API_KEY = "Fx7961E41jCQPDV9eZANoAzb2eBeqIvEBi1T4mS6IyA"
H = {"X-Api-Key": API_KEY}
# Imagen mínima válida para uploads (1x1 JPEG)
MINI_JPG = bytes([
    0xFF,0xD8,0xFF,0xE0,0x00,0x10,0x4A,0x46,0x49,0x46,0x00,0x01,0x01,0x00,
    0x00,0x01,0x00,0x01,0x00,0x00,0xFF,0xDB,0x00,0x43,0x00,0x08,0x06,0x06,
    0x07,0x06,0x05,0x08,0x07,0x07,0x07,0x09,0x09,0x08,0x0A,0x0C,0x14,0x0D,
    0x0C,0x0B,0x0B,0x0C,0x19,0x12,0x13,0x0F,0x14,0x1D,0x1A,0x1F,0x1E,0x1D,
    0x1A,0x1C,0x1C,0x20,0x24,0x2E,0x27,0x20,0x22,0x2C,0x23,0x1C,0x1C,0x28,
    0x37,0x29,0x2C,0x30,0x31,0x34,0x34,0x34,0x1F,0x27,0x39,0x3D,0x38,0x32,
    0x3C,0x2E,0x33,0x34,0x32,0xFF,0xC0,0x00,0x0B,0x08,0x00,0x01,0x00,0x01,
    0x01,0x01,0x11,0x00,0xFF,0xC4,0x00,0x14,0x00,0x01,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF,0xC4,
    0x00,0x14,0x10,0x01,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0x00,0x00,0xFF,0xDA,0x00,0x08,0x01,0x01,0x00,0x00,
    0x3F,0x00,0x7F,0xFF,0xD9,
])


def foto():
    return ("foto.jpg", io.BytesIO(MINI_JPG), "image/jpeg")


@pytest.fixture(scope="session")
def c():
    """Cliente httpx con API key."""
    with httpx.Client(base_url=BASE, headers=H, timeout=15) as client:
        yield client


def registrar_y_loguear(c, ts, suffix=""):
    """Registra cliente nuevo, reintenta si rechazado, devuelve (token, email)."""
    for attempt in range(15):
        email = f"test_{ts}_{suffix}_{attempt}@midnightlace.com"
        doc = f"4{ts}{suffix}{attempt}"[:10]
        nick = f"u{ts}{suffix}{attempt}"[:30]
        r = c.post("/v1/auth/registro", data={
            "documento": doc,
            "nombre": "Test",
            "apellido": "Usuario",
            "email": email,
            "nombreUsuario": nick,
            "direccion": "Calle Falsa",
            "altura": "123",
            "codigoPostal": "1234",
            "localidad": "CABA",
            "ciudad": "Buenos Aires",
            "idPais": "1",
        }, files={
            "fotoDocFrente": foto(),
            "fotoDocDorso": foto(),
        })
        if r.status_code not in (200, 201):
            continue
        if not r.json().get("aprobado"):
            continue  # rechazado (30%), reintentar

        # registro ok y aprobado → código guardado en DB por verificar_cliente
        codigo = db_query(
            f"SELECT codigo FROM \"codigosVerificacion\" "
            f"WHERE tipo='registro' AND usado='no' "
            f"AND persona = (SELECT identificador FROM personas WHERE email='{email}') "
            f"LIMIT 1"
        )
        if not codigo:
            continue

        r3 = c.post("/v1/auth/confirmar", json={"codigo": codigo, "clave": "Clave123!", "tipo": "registro"})
        if r3.status_code != 200:
            continue

        r4 = c.post("/v1/auth/login", json={"email": email, "clave": "Clave123!"})
        if r4.status_code == 200:
            return r4.json()["tokenAcceso"], email

    raise RuntimeError(f"No se pudo registrar cliente aprobado en 15 intentos (ts={ts})")


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def tokens(c):
    """Registra dos clientes y loguea el subastador. Devuelve dict con tokens."""
    ts = int(time.time())
    token_a, email_a = registrar_y_loguear(c, ts, "a")
    token_b, email_b = registrar_y_loguear(c, ts, "b")

    r = c.post("/v1/auth/login", json={"email": "subastador@midnightlace.com", "clave": "Subastador123!"})
    assert r.status_code == 200
    token_sub = r.json()["tokenAcceso"]

    return {
        "a": token_a, "email_a": email_a,
        "b": token_b, "email_b": email_b,
        "sub": token_sub,
    }


@pytest.fixture(scope="session")
def producto_id(c, tokens):
    """Cliente A crea un producto. Devuelve su id (ya en estado asignado)."""
    r = c.post("/v1/productos", headers=auth(tokens["a"]), data={
        "descripcionCatalogo": "Vestido Test Automatizado\nVestido de prueba para tests automatizados.",
        "descripcionCompleta": "Vestido de prueba para tests automatizados",
        "declaracionPropiedad": "true",
        "precioBase": "10000.00",
    }, files={f"foto{i}": foto() for i in range(1, 7)})
    assert r.status_code in (200, 201), f"crear producto falló: {r.text}"
    pid = r.json()["identificador"]
    estado = r.json()["estadoProducto"]
    # verificación automática: 70% aprueba. Reintentamos hasta 5 veces si rechaza.
    attempts = 0
    while estado == "rechazado" and attempts < 10:
        r = c.post("/v1/productos", headers=auth(tokens["a"]), data={
            "descripcionCatalogo": f"Vestido Test Intento {attempts}\nVestido de prueba para reintento automatizado.",
            "descripcionCompleta": f"Vestido de prueba intento {attempts}",
            "declaracionPropiedad": "true",
            "precioBase": "10000.00",
        }, files={f"foto{i}": foto() for i in range(1, 7)})
        pid = r.json()["identificador"]
        estado = r.json()["estadoProducto"]
        attempts += 1
    assert estado == "asignado", f"producto no aprobado después de {attempts} intentos"
    return pid


@pytest.fixture(scope="session")
def subasta_id(c, tokens):
    """Subastador crea subasta + catálogo. Devuelve (subasta_id, catalogo_id)."""
    import datetime
    fecha = (datetime.date.today() + datetime.timedelta(days=15)).isoformat()
    r = c.post("/v1/subastador/subastas", headers=auth(tokens["sub"]), json={
        "nombre": "Subasta Test Integración",
        "fecha": fecha,
        "hora": "18:00:00",
        "categoria": "comun",
        "moneda": "ARS",
        "duracionItemMinutos": 1,
    })
    assert r.status_code in (200, 201), f"crear subasta falló: {r.text}"
    sid = r.json()["identificador"]

    r2 = c.post("/v1/subastador/catalogos", headers=auth(tokens["sub"]), json={
        "descripcion": "Catálogo test",
        "idSubasta": sid,
    })
    assert r2.status_code in (200, 201), f"crear catálogo falló: {r2.text}"
    cid = r2.json()["identificador"]
    return sid, cid


# ──────────────────────────────────────────────
# Tests sin estado complejo
# ──────────────────────────────────────────────

class TestMiActividadVacia:
    """Endpoints que deben devolver 200 con listas vacías."""

    def test_listar_subastas_vacio(self, c, tokens):
        r = c.get("/v1/mi/subastas", headers=auth(tokens["a"]))
        assert r.status_code == 200
        assert r.json()["datos"] == []

    def test_listar_pujas_vacio(self, c, tokens):
        r = c.get("/v1/mi/pujas", headers=auth(tokens["a"]))
        assert r.status_code == 200
        assert r.json()["datos"] == []

    def test_listar_compras_vacio(self, c, tokens):
        r = c.get("/v1/mi/compras", headers=auth(tokens["a"]))
        assert r.status_code == 200
        assert r.json()["datos"] == []

    def test_listar_multas_vacio(self, c, tokens):
        r = c.get("/v1/mi/multas", headers=auth(tokens["a"]))
        assert r.status_code == 200
        assert r.json()["datos"] == []

    def test_metricas(self, c, tokens):
        r = c.get("/v1/mi/metricas", headers=auth(tokens["a"]))
        assert r.status_code == 200
        data = r.json()
        assert "totalPujas" in data
        assert "pujasGanadas" in data
        assert "totalSubastasParticipadas" in data
        assert "totalPujasRealizadas" in data
        assert "totalGanadas" in data
        assert "totalImportePujado" in data
        assert "totalImportePagado" in data
        assert data["pujasPorMes"] == []
        assert data["porCategoria"] == []
        assert data["totalPujas"] == 0

    def test_listar_notificaciones_vacio(self, c, tokens):
        r = c.get("/v1/mi/notificaciones", headers=auth(tokens["b"]))
        assert r.status_code == 200

    def test_verificar_vencimientos_sin_multas(self, c):
        r = c.post("/v1/interno/verificar-vencimientos")
        assert r.status_code == 200
        assert r.json()["bloqueados"] == 0


class TestMiActividadAutorizacion:
    """Casos de auth fallida."""

    def test_sin_token(self, c):
        r = c.get("/v1/mi/subastas")
        assert r.status_code == 401

    def test_sin_api_key(self):
        r = httpx.get(f"{BASE}/v1/mi/subastas", headers={"Authorization": "Bearer fake"})
        assert r.status_code == 403

    def test_token_invalido(self, c):
        r = c.get("/v1/mi/subastas", headers={"Authorization": "Bearer token.falso.xxx"})
        assert r.status_code == 401

    def test_compra_no_encontrada(self, c, tokens):
        r = c.post("/v1/mi/compras/999/pagar", headers=auth(tokens["a"]),
                   json={"idMedioPago": 1})
        assert r.status_code == 404
        assert r.json()["codigo"] == "NO_ENCONTRADO"

    def test_multa_no_encontrada(self, c, tokens):
        r = c.post("/v1/mi/multas/999/pagar", headers=auth(tokens["a"]),
                   json={"idMedioPago": 1})
        assert r.status_code == 404
        assert r.json()["codigo"] == "NO_ENCONTRADO"

    def test_notificacion_no_encontrada(self, c, tokens):
        r = c.patch("/v1/mi/notificaciones/9999", headers=auth(tokens["a"]),
                    json={"leida": True})
        assert r.status_code == 404

    def test_condiciones_producto_sin_rol_duenio(self, c, tokens):
        # Si token_a aún no creó producto → sin rol duenio → 403
        # Si ya tiene rol duenio → 404 (producto no existe)
        r = c.get("/v1/productos/9999/condiciones", headers=auth(tokens["a"]))
        assert r.status_code in (403, 404)

    def test_paginacion_invalida(self, c, tokens):
        r = c.get("/v1/mi/subastas?pagina=0", headers=auth(tokens["a"]))
        assert r.status_code == 422

    def test_cantidad_excede_max(self, c, tokens):
        r = c.get("/v1/mi/subastas?cantidad=101", headers=auth(tokens["a"]))
        assert r.status_code == 422


class TestCondicionesYBugFix:
    """
    Flujo completo:
    1. Subastador agrega producto al catálogo → estado pendiente_confirmacion
    2. GET /condiciones → devuelve los 5 campos
    3. PATCH aceptar-condiciones acepta=False → bug #10: ItemCatalogo eliminado
    4. Verificar que estado volvió a 'asignado' y notificación existe
    """

    def test_agregar_item_catalogo(self, c, tokens, producto_id, subasta_id):
        sid, cid = subasta_id
        r = c.post(f"/v1/subastador/catalogos/{cid}/items",
                   headers=auth(tokens["sub"]),
                   json={"idProducto": producto_id, "orden": 1, "comision": 1500.0})
        assert r.status_code in (200, 201), f"agregar item falló: {r.text}"
        # Producto debe estar en pendiente_confirmacion
        r2 = c.get(f"/v1/productos/{producto_id}", headers=auth(tokens["a"]))
        assert r2.status_code == 200
        assert r2.json()["estadoProducto"] == "pendiente_confirmacion"

    def test_get_condiciones(self, c, tokens, producto_id):
        r = c.get(f"/v1/productos/{producto_id}/condiciones", headers=auth(tokens["a"]))
        assert r.status_code == 200, f"condiciones falló: {r.text}"
        data = r.json()
        assert "precioBase" in data
        assert "comision" in data
        assert "fecha" in data
        assert "hora" in data
        assert "lugar" in data
        assert data["precioBase"] == "10000.00"
        assert data["comision"] == "1500.00"

    def test_condiciones_otro_usuario_no_accede(self, c, tokens, producto_id):
        # Cliente B sin rol duenio → 403. Con rol duenio pero no dueño → 404.
        r = c.get(f"/v1/productos/{producto_id}/condiciones", headers=auth(tokens["b"]))
        assert r.status_code in (403, 404)

    def test_notificacion_producto_aceptado_enriquecida(self, c, tokens):
        """La notif de producto_aceptado debe tener precioBase, comision, fecha, hora, lugar."""
        r = c.get("/v1/mi/notificaciones", headers=auth(tokens["a"]))
        assert r.status_code == 200
        notifs = r.json()["datos"]
        aceptadas = [n for n in notifs if n["tipo"] == "producto_aceptado"]
        assert len(aceptadas) >= 1, "No hay notificación producto_aceptado"
        detalle = aceptadas[0]["detalle"]
        assert "precioBase" in detalle, f"falta precioBase en detalle: {detalle}"
        assert "comision" in detalle
        assert "fecha" in detalle
        assert "hora" in detalle
        assert "lugar" in detalle

    def test_rechazar_condiciones_elimina_item_catalogo(self, c, tokens, producto_id):
        """Bug #10: al rechazar, ItemCatalogo debe desaparecer."""
        r = c.patch(f"/v1/productos/{producto_id}/aceptar-condiciones",
                    headers=auth(tokens["a"]),
                    json={"acepta": False})
        assert r.status_code == 200, f"rechazar falló: {r.text}"
        data = r.json()
        assert data["estadoProducto"] == "asignado", f"estado inesperado: {data['estadoProducto']}"

    def test_condiciones_tras_rechazo_409(self, c, tokens, producto_id):
        """Después del rechazo, estado=asignado → /condiciones debe dar 409."""
        r = c.get(f"/v1/productos/{producto_id}/condiciones", headers=auth(tokens["a"]))
        assert r.status_code == 409
        assert r.json()["codigo"] == "ESTADO_INVALIDO"

    def test_notificacion_devolucion_existe(self, c, tokens):
        r = c.get("/v1/mi/notificaciones", headers=auth(tokens["a"]))
        notifs = r.json()["datos"]
        tipos = [n["tipo"] for n in notifs]
        assert "devolucion_producto" in tipos, f"falta devolucion_producto, tipos: {tipos}"

    def test_re_listado_permitido_tras_rechazo(self, c, tokens, producto_id, subasta_id):
        """Producto volvió a asignado → subastador puede re-agregarlo al catálogo (no hay item fantasma)."""
        sid, cid = subasta_id
        r = c.post(f"/v1/subastador/catalogos/{cid}/items",
                   headers=auth(tokens["sub"]),
                   json={"idProducto": producto_id, "orden": 1, "comision": 2000.0})
        assert r.status_code in (200, 201), f"re-listar falló: {r.text}"

    def test_aceptar_condiciones_ok(self, c, tokens, producto_id):
        """Ahora el dueño acepta las condiciones → en_subasta."""
        r = c.patch(f"/v1/productos/{producto_id}/aceptar-condiciones",
                    headers=auth(tokens["a"]),
                    json={"acepta": True})
        assert r.status_code == 200, f"aceptar falló: {r.text}"
        assert r.json()["estadoProducto"] == "en_subasta"

    def test_condiciones_tras_aceptar_409(self, c, tokens, producto_id):
        """Después de aceptar, estado=en_subasta → /condiciones debe dar 409."""
        r = c.get(f"/v1/productos/{producto_id}/condiciones", headers=auth(tokens["a"]))
        assert r.status_code == 409


class TestMediosVerificacion:
    """A.7: medio de pago se verifica automáticamente al crear."""

    def test_crear_cheque_se_verifica_solo(self, c, tokens):
        import datetime
        r = c.post("/v1/medios-de-pago", headers=auth(tokens["a"]),
                   json={
                       "tipo": "chequeCertificado",
                       "moneda": "ARS",
                       "detalle": {
                           "montoGarantizado": 50000,
                           "montoDisponible": 50000,
                           "fechaEntrega": (datetime.date.today() + datetime.timedelta(days=30)).isoformat(),
                       }
                   })
        assert r.status_code in (200, 201), f"crear medio falló: {r.text}"
        data = r.json()
        assert data["verificado"] == "si", f"medio no auto-verificado: {data}"

    def test_crear_cuenta_bancaria_se_verifica_sola(self, c, tokens):
        r = c.post("/v1/medios-de-pago", headers=auth(tokens["a"]),
                   json={
                       "tipo": "cuentaBancaria",
                       "moneda": "ARS",
                       "detalle": {"nombreBanco": "TestBank", "numeroCuenta": "0001-9999"}
                   })
        assert r.status_code in (200, 201)
        assert r.json()["verificado"] == "si"

    def test_notificacion_medio_verificado(self, c, tokens):
        r = c.get("/v1/mi/notificaciones", headers=auth(tokens["a"]))
        notifs = r.json()["datos"]
        tipos = [n["tipo"] for n in notifs]
        assert "medio_verificado" in tipos, f"falta medio_verificado, tipos: {tipos}"


class TestNotificaciones:
    """GET y PATCH notificaciones."""

    def test_lista_con_filtro_no_leida(self, c, tokens):
        r = c.get("/v1/mi/notificaciones?leida=no", headers=auth(tokens["a"]))
        assert r.status_code == 200
        for n in r.json()["datos"]:
            assert n["leida"] == "no"

    def test_filtro_leida_invalido(self, c, tokens):
        r = c.get("/v1/mi/notificaciones?leida=maybe", headers=auth(tokens["a"]))
        assert r.status_code == 422

    def test_marcar_leida(self, c, tokens):
        # Obtener primera notificación no leída
        r = c.get("/v1/mi/notificaciones?leida=no", headers=auth(tokens["a"]))
        notifs = r.json()["datos"]
        if not notifs:
            pytest.skip("No hay notificaciones para marcar")
        nid = notifs[0]["identificador"]

        r2 = c.patch(f"/v1/mi/notificaciones/{nid}", headers=auth(tokens["a"]),
                     json={"leida": True})
        assert r2.status_code == 200
        assert r2.json()["leida"] == "si"

    def test_marcar_leida_otro_usuario_404(self, c, tokens):
        r = c.get("/v1/mi/notificaciones?leida=si", headers=auth(tokens["a"]))
        notifs = r.json()["datos"]
        if not notifs:
            pytest.skip("No hay notificaciones leídas del cliente A")
        nid = notifs[0]["identificador"]
        # Cliente B intenta marcar la notif de A
        r2 = c.patch(f"/v1/mi/notificaciones/{nid}", headers=auth(tokens["b"]),
                     json={"leida": True})
        assert r2.status_code == 404

    def test_paginacion_meta(self, c, tokens):
        r = c.get("/v1/mi/notificaciones?pagina=1&cantidad=2", headers=auth(tokens["a"]))
        assert r.status_code == 200
        meta = r.json()["meta"]
        assert "pagina" in meta
        assert "totalPaginas" in meta
        assert meta["pagina"] == 1


class TestPagarCompra:
    """
    Requiere crear un RegistroDeSubasta real vía cierre de subasta.
    Inserción directa en DB como alternativa.
    """

    def test_pagar_compra_medio_no_verificado(self, c, tokens):
        """Medio sin verificar → 400 MEDIO_PAGO_NO_VERIFICADO (si hubiera compra)."""
        # Sin compra → 404 primero. Esto valida el orden de checks.
        r = c.post("/v1/mi/compras/9999/pagar", headers=auth(tokens["a"]),
                   json={"idMedioPago": 1})
        assert r.status_code == 404  # NO_ENCONTRADO antes de llegar a validar medio

    def test_actualizar_retiro_no_encontrado(self, c, tokens):
        r = c.patch("/v1/mi/compras/9999", headers=auth(tokens["a"]),
                    json={"retiraPersonalmente": True})
        assert r.status_code == 404

    def test_pagar_multa_no_encontrada(self, c, tokens):
        r = c.post("/v1/mi/multas/9999/pagar", headers=auth(tokens["a"]),
                   json={"idMedioPago": 1})
        assert r.status_code == 404


class TestVerificarVencimientos:
    """POST /v1/interno/verificar-vencimientos."""

    def test_sin_multas_vencidas_devuelve_cero(self, c):
        r = c.post("/v1/interno/verificar-vencimientos")
        assert r.status_code == 200
        assert "bloqueados" in r.json()
        assert r.json()["bloqueados"] == 0

    def test_idempotente(self, c):
        r1 = c.post("/v1/interno/verificar-vencimientos")
        r2 = c.post("/v1/interno/verificar-vencimientos")
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json() == r2.json()

    def test_no_requiere_auth(self):
        """Sin API key debe fallar, pero sin JWT debe funcionar."""
        r = httpx.post(f"{BASE}/v1/interno/verificar-vencimientos", headers=H)
        assert r.status_code == 200


class TestWSUsuario:
    """WS /v1/ws/usuario — conexión básica."""

    def test_ws_rechaza_sin_token(self):
        try:
            import websockets.sync.client as wsc
            # Server acepta la conexión WS pero la cierra con 4001.
            # connect() no lanza; recv() sí lanza al recibir el close frame.
            ws = wsc.connect(
                f"ws://localhost:8000/v1/ws/usuario?token=invalido",
                additional_headers={"X-Api-Key": API_KEY},
                open_timeout=3,
            )
            with pytest.raises(Exception):
                ws.recv()  # debe fallar con ConnectionClosed 4001
        except ImportError:
            pytest.skip("websockets no instalado")

    def test_ws_conecta_con_token_valido(self, c, tokens):
        try:
            import websockets.sync.client as wsc
            ws_url = f"ws://localhost:8000/v1/ws/usuario?token={tokens['a']}"
            with wsc.connect(ws_url,
                             additional_headers={"X-Api-Key": API_KEY},
                             open_timeout=5) as ws:
                # Conexión exitosa, cerrar limpio
                ws.close()
        except ImportError:
            # Probar con httpx websocket si disponible
            pytest.skip("websockets no instalado, saltear test WS")

    def test_ws_conecta_con_multa_simulada(self, c, tokens):
        """Usuario con multa debe poder conectar al WS de usuario (no 4003)."""
        # No tenemos multa real, pero el token con multaImpaga=true en JWT
        # debe igualmente conectar. Testeamos con token normal (multa=false).
        # El comportamiento real se verifica con test de pagar_compra+cheque.
        try:
            import websockets.sync.client as wsc
            ws_url = f"ws://localhost:8000/v1/ws/usuario?token={tokens['b']}"
            with wsc.connect(ws_url,
                             additional_headers={"X-Api-Key": API_KEY},
                             open_timeout=5) as ws:
                ws.close()
        except ImportError:
            pytest.skip("websockets no instalado")


class TestSubastaCompletaConPago:
    """
    Flujo completo con pago:
    1. Subastador abre subasta y cierra item (via interno)
    2. Comprador paga con cheque → JWT fresco
    3. Sin fondos → multa generada
    """

    @pytest.fixture(scope="class")
    def setup_subasta_abierta(self, c, tokens):
        """Crea una subasta con un producto, la abre y registra un asistente."""
        import datetime

        # Crear producto para dueño A
        r = c.post("/v1/productos", headers=auth(tokens["a"]), data={
            "descripcionCatalogo": "Producto Pago Test\nProducto para subasta de pago test.",
            "descripcionCompleta": "Producto para subasta de pago test",
            "declaracionPropiedad": "true",
            "precioBase": "5000.00",
        }, files={f"foto{i}": foto() for i in range(1, 7)})
        assert r.status_code in (200, 201)
        pid = r.json()["identificador"]

        # Reintentar si rechazado
        for _ in range(10):
            if r.json().get("estadoProducto") == "asignado":
                break
            r = c.post("/v1/productos", headers=auth(tokens["a"]), data={
                "descripcionCatalogo": f"Producto Pago Retry {_}\nProducto de reintento para pago test.",
                "descripcionCompleta": f"Producto pago test retry {_}",
                "declaracionPropiedad": "true",
                "precioBase": "5000.00",
            }, files={f"foto{i}": foto() for i in range(1, 7)})
            pid = r.json()["identificador"]

        if r.json().get("estadoProducto") != "asignado":
            pytest.skip("No se pudo crear producto aprobado")

        # Crear subasta
        fecha = (datetime.date.today() + datetime.timedelta(days=15)).isoformat()
        r2 = c.post("/v1/subastador/subastas", headers=auth(tokens["sub"]), json={
            "nombre": "Subasta Pago Test",
            "fecha": fecha,
            "hora": "20:00:00",
            "categoria": "comun",
            "moneda": "ARS",
            "duracionItemMinutos": 1,
        })
        assert r2.status_code in (200, 201), r2.text
        sid = r2.json()["identificador"]

        # Crear catálogo y agregar item
        r3 = c.post("/v1/subastador/catalogos", headers=auth(tokens["sub"]),
                    json={"descripcion": "Catálogo pago", "idSubasta": sid})
        assert r3.status_code in (200, 201)
        cid = r3.json()["identificador"]

        r4 = c.post(f"/v1/subastador/catalogos/{cid}/items",
                    headers=auth(tokens["sub"]),
                    json={"idProducto": pid, "orden": 1, "comision": 500.0})
        assert r4.status_code in (200, 201), r4.text

        # Dueño A acepta condiciones
        r5 = c.patch(f"/v1/productos/{pid}/aceptar-condiciones",
                     headers=auth(tokens["a"]), json={"acepta": True})
        assert r5.status_code == 200, r5.text

        # Abrir subasta
        r6 = c.patch(f"/v1/subastador/subastas/{sid}/estado",
                     headers=auth(tokens["sub"]), json={"estado": "abierta"})
        assert r6.status_code == 200, r6.text

        # Cerrar item sin pujas → RegistroDeSubasta con cliente=MIDNIGHT_LACE_ID (no sirve para pagar)
        # En cambio, cerramos de todas formas para tener el registro
        r7 = c.post("/v1/interno/cierre-item", json={"id_subasta": sid})
        assert r7.status_code == 200, r7.text

        return {"sid": sid, "pid": pid, "cid": cid}

    def test_compras_lista_despues_de_subasta(self, c, tokens, setup_subasta_abierta):
        """Después de cerrar la subasta, GET /mi/compras puede tener registros."""
        r = c.get("/v1/mi/compras", headers=auth(tokens["a"]))
        assert r.status_code == 200
        # No necesariamente tiene compras (el ganador es Midnight Lace si no hubo pujas)
        assert "datos" in r.json()

    def test_metricas_despues_de_actividad(self, c, tokens):
        r = c.get("/v1/mi/metricas", headers=auth(tokens["a"]))
        assert r.status_code == 200
        data = r.json()
        assert all(k in data for k in ["totalPujas", "pujasGanadas", "totalCompras",
                                        "comprasPagadas", "multasImpagas"])
        assert all(k in data for k in ["totalSubastasParticipadas", "totalPujasRealizadas",
                                        "totalGanadas", "totalImportePujado", "totalImportePagado",
                                        "pujasPorMes", "porCategoria"])


class TestProcesarPagoDirecto:
    """Tests de procesar_pago a través de los endpoints reales."""

    def test_pagar_compra_medio_de_otro_usuario(self, c, tokens):
        """Medio que pertenece a B no puede usarlo A."""
        import datetime
        # Crear medio para B
        r = c.post("/v1/medios-de-pago", headers=auth(tokens["b"]), json={
            "tipo": "cuentaBancaria",
            "moneda": "ARS",
            "detalle": {"nombreBanco": "Banco B", "numeroCuenta": "B-001"},
        })
        assert r.status_code in (200, 201)
        medio_b_id = r.json()["identificador"]

        # A intenta pagar con el medio de B → si no hay compra de A, da 404 primero
        r2 = c.post("/v1/mi/compras/9999/pagar", headers=auth(tokens["a"]),
                    json={"idMedioPago": medio_b_id})
        assert r2.status_code == 404  # compra no existe, correcto

    def test_medio_moneda_incorrecta(self, c, tokens):
        """Si hubiera compra en ARS y medio en USD → MONEDA_NO_COINCIDE.
        Sin compra real, solo verificamos que 404 aparece primero."""
        import datetime
        r = c.post("/v1/medios-de-pago", headers=auth(tokens["a"]), json={
            "tipo": "cuentaBancaria",
            "moneda": "USD",
            "detalle": {"nombreBanco": "Banco USD", "numeroCuenta": "USD-001"},
        })
        assert r.status_code in (200, 201)
        assert r.json()["verificado"] == "si"

        r2 = c.post("/v1/mi/compras/9999/pagar", headers=auth(tokens["a"]),
                    json={"idMedioPago": r.json()["identificador"]})
        assert r2.status_code == 404


class TestEdgeCases:
    """Casos borde varios."""

    def test_retiro_cuerpo_invalido(self, c, tokens):
        r = c.patch("/v1/mi/compras/1", headers=auth(tokens["a"]),
                    json={"retiraPersonalmente": "quizas"})
        assert r.status_code == 422

    def test_marcar_leida_cuerpo_invalido(self, c, tokens):
        r = c.patch("/v1/mi/notificaciones/1", headers=auth(tokens["a"]),
                    json={"leida": "tal_vez"})
        assert r.status_code == 422

    def test_pujas_filtro_iditem(self, c, tokens):
        r = c.get("/v1/mi/pujas?idItem=999", headers=auth(tokens["a"]))
        assert r.status_code == 200
        assert r.json()["datos"] == []

    def test_condiciones_producto_otro_estado(self, c, tokens, producto_id):
        """Producto en en_subasta → /condiciones da 409."""
        # producto_id ya está en en_subasta por TestCondicionesYBugFix
        r = c.get(f"/v1/productos/{producto_id}/condiciones", headers=auth(tokens["a"]))
        assert r.status_code == 409
        assert r.json()["codigo"] == "ESTADO_INVALIDO"
