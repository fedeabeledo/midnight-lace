"""
Tests integración — Cuentas de cobro del dueño.
Requiere server en localhost:8000 (Docker).
"""
import io
import subprocess
import time
import pytest
import httpx

BASE = "http://localhost:8000"
KEY = "Fx7961E41jCQPDV9eZANoAzb2eBeqIvEBi1T4mS6IyA"
H = {"X-Api-Key": KEY}
DB_URL = "postgresql://midnightlace:midnightlace@localhost:5432/midnightlace"

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


def db_query(sql):
    r = subprocess.run(
        ["psql", DB_URL, "-t", "-A", "-c", sql],
        capture_output=True, text=True,
    )
    return r.stdout.strip()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def registrar_y_loguear(c, ts, suffix=""):
    for attempt in range(15):
        email = f"cc_{ts}_{suffix}_{attempt}@midnightlace.com"
        doc = f"5{ts}{suffix}{attempt}"[:10]
        nick = f"cc{ts}{suffix}{attempt}"[:30]
        r = c.post("/v1/auth/registro", data={
            "documento": doc, "nombre": "Test", "apellido": "CC",
            "email": email, "nombreUsuario": nick,
            "direccion": "Calle", "altura": "1", "codigoPostal": "1234",
            "localidad": "CABA", "ciudad": "BsAs", "idPais": "1",
        }, files={"fotoDocFrente": foto(), "fotoDocDorso": foto()})
        if r.status_code not in (200, 201) or not r.json().get("aprobado"):
            continue
        codigo = db_query(
            f"SELECT codigo FROM \"codigosVerificacion\" "
            f"WHERE tipo='registro' AND usado='no' "
            f"AND persona=(SELECT identificador FROM personas WHERE email='{email}') LIMIT 1"
        )
        if not codigo:
            continue
        r3 = c.post("/v1/auth/confirmar", json={"codigo": codigo, "clave": "Clave123!", "tipo": "registro"})
        if r3.status_code != 200:
            continue
        r4 = c.post("/v1/auth/login", json={"email": email, "clave": "Clave123!"})
        if r4.status_code == 200:
            return r4.json()["tokenAcceso"], email
    raise RuntimeError("No se pudo registrar usuario aprobado")


@pytest.fixture(scope="session")
def c():
    with httpx.Client(base_url=BASE, headers=H, timeout=15) as client:
        yield client


@pytest.fixture(scope="session")
def tokens(c):
    ts = int(time.time())
    # Dueño: necesita crear al menos un producto para obtener rol duenio
    token_duenio, _ = registrar_y_loguear(c, ts, "d")
    # Comprador sin producto (sin rol duenio)
    token_comprador, _ = registrar_y_loguear(c, ts, "c")
    return {"duenio": token_duenio, "comprador": token_comprador}


@pytest.fixture(scope="session")
def token_duenio_con_rol(c, tokens):
    """Crea un producto para que el usuario obtenga rol duenio."""
    token = tokens["duenio"]
    for _ in range(15):
        r = c.post("/v1/productos", headers=auth(token), data={
            "descripcionCompleta": "Producto test cuentas cobro",
            "declaracionPropiedad": "true",
            "precioBase": "5000.00",
        }, files={f"foto{i}": foto() for i in range(1, 7)})
        if r.status_code in (200, 201) and r.json().get("estadoProducto") == "asignado":
            break
    return token


CUENTA_BASE = {
    "nombreBanco": "Banco Nación",
    "numeroCuenta": "0000-0001-1234567890",
    "moneda": "ARS",
}


class TestCuentasCobroAuth:
    def test_sin_token_401(self, c):
        r = c.get("/v1/duenio/cuentas-cobro")
        assert r.status_code == 401

    def test_comprador_sin_duenio_403(self, c, tokens):
        r = c.get("/v1/duenio/cuentas-cobro", headers=auth(tokens["comprador"]))
        assert r.status_code == 403

    def test_comprador_no_puede_crear_403(self, c, tokens):
        r = c.post("/v1/duenio/cuentas-cobro", headers=auth(tokens["comprador"]),
                   json=CUENTA_BASE)
        assert r.status_code == 403

    def test_comprador_no_puede_borrar_403(self, c, tokens):
        r = c.delete("/v1/duenio/cuentas-cobro/999", headers=auth(tokens["comprador"]))
        assert r.status_code == 403


class TestCuentasCobro:
    def test_lista_vacia(self, c, token_duenio_con_rol):
        r = c.get("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol))
        assert r.status_code == 200
        assert r.json()["datos"] == []
        assert "meta" in r.json()

    def test_crear_sin_pais(self, c, token_duenio_con_rol):
        r = c.post("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol),
                   json=CUENTA_BASE)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["nombreBanco"] == "Banco Nación"
        assert data["numeroCuenta"] == "0000-0001-1234567890"
        assert data["moneda"] == "ARS"
        assert data["idPais"] is None
        assert data["activa"] == "si"
        assert "identificador" in data

    def test_crear_con_pais(self, c, token_duenio_con_rol):
        r = c.post("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol),
                   json={**CUENTA_BASE, "idPais": 1})
        assert r.status_code == 201
        assert r.json()["idPais"] == 1

    def test_lista_muestra_activas(self, c, token_duenio_con_rol):
        r = c.get("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol))
        assert r.status_code == 200
        datos = r.json()["datos"]
        assert len(datos) == 2
        for d in datos:
            assert d["activa"] == "si"

    def test_paginacion_meta(self, c, token_duenio_con_rol):
        r = c.get("/v1/duenio/cuentas-cobro?pagina=1&cantidad=1",
                  headers=auth(token_duenio_con_rol))
        assert r.status_code == 200
        meta = r.json()["meta"]
        assert meta["pagina"] == 1
        assert meta["total"] == 2
        assert meta["totalPaginas"] == 2
        assert len(r.json()["datos"]) == 1

    def test_delete_exitoso(self, c, token_duenio_con_rol):
        # Crear una cuenta nueva para borrar
        r_crear = c.post("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol),
                         json={**CUENTA_BASE, "nombreBanco": "Banco a borrar"})
        assert r_crear.status_code == 201
        cuenta_id = r_crear.json()["identificador"]

        r_del = c.delete(f"/v1/duenio/cuentas-cobro/{cuenta_id}",
                         headers=auth(token_duenio_con_rol))
        assert r_del.status_code == 204

    def test_delete_desaparece_del_list(self, c, token_duenio_con_rol):
        # Crear y borrar
        r_crear = c.post("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol),
                         json={**CUENTA_BASE, "nombreBanco": "Banco temporal"})
        cuenta_id = r_crear.json()["identificador"]
        c.delete(f"/v1/duenio/cuentas-cobro/{cuenta_id}", headers=auth(token_duenio_con_rol))

        # No aparece en lista
        r = c.get("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol))
        ids = [d["identificador"] for d in r.json()["datos"]]
        assert cuenta_id not in ids

    def test_delete_no_borra_fila_db(self, c, token_duenio_con_rol):
        """Soft delete: fila sigue en DB con activa='no'."""
        r_crear = c.post("/v1/duenio/cuentas-cobro", headers=auth(token_duenio_con_rol),
                         json={**CUENTA_BASE, "nombreBanco": "Soft delete test"})
        cuenta_id = r_crear.json()["identificador"]
        c.delete(f"/v1/duenio/cuentas-cobro/{cuenta_id}", headers=auth(token_duenio_con_rol))

        activa = db_query(
            f"SELECT activa FROM \"cuentasCobro\" WHERE identificador={cuenta_id}"
        )
        assert activa == "no", f"fila borrada fisicamente o activa={activa}"

    def test_delete_no_encontrado(self, c, token_duenio_con_rol):
        r = c.delete("/v1/duenio/cuentas-cobro/999999",
                     headers=auth(token_duenio_con_rol))
        assert r.status_code == 404
        assert r.json()["codigo"] == "NO_ENCONTRADO"

    def test_paginacion_invalida(self, c, token_duenio_con_rol):
        r = c.get("/v1/duenio/cuentas-cobro?pagina=0",
                  headers=auth(token_duenio_con_rol))
        assert r.status_code == 422

    def test_cantidad_excede_max(self, c, token_duenio_con_rol):
        r = c.get("/v1/duenio/cuentas-cobro?cantidad=101",
                  headers=auth(token_duenio_con_rol))
        assert r.status_code == 422
