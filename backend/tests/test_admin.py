"""
Tests integración — endpoints Admin (empleado).
Requiere server en localhost:8000 (Docker).
"""
import subprocess
import time
import pytest
import httpx

BASE = "http://localhost:8000"
KEY = "Fx7961E41jCQPDV9eZANoAzb2eBeqIvEBi1T4mS6IyA"
H = {"X-Api-Key": KEY}
DB_URL = "postgresql://midnightlace:midnightlace@localhost:5432/midnightlace"


def db_run(sql):
    r = subprocess.run(["psql", DB_URL, "-c", sql], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"psql error: {r.stderr.strip()}")


def db_query(sql):
    r = subprocess.run(["psql", DB_URL, "-t", "-A", "-c", sql], capture_output=True, text=True)
    return r.stdout.strip()


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def c():
    with httpx.Client(base_url=BASE, headers=H, timeout=15) as client:
        yield client


@pytest.fixture(scope="session")
def token_empleado(c):
    """Crea un empleado de prueba directo en DB y loguea."""
    ts = int(time.time())
    email = f"admin_{ts}@midnightlace.com"
    nick = f"admin_{ts}"[:30]

    # Hashear clave usando el endpoint de crear_subastador (reutilizamos el hash de security.py)
    # Alternativa: insertar con contraseña conocida via crear_subastador si ya tenemos empleado...
    # Pero no tenemos empleado con login. Insertamos persona + empleado directo via SQL con hash bcrypt.
    # Hash de "Admin123!" generado con bcrypt (60 chars).
    # Usamos psql para llamar al server: en su lugar, creamos via API con el empleado ID 1 que existe
    # (pero no puede loguear). Mejor: insertar via psql con hash conocido.
    # Hash de "Admin123!" = $2b$12$... — generamos con python en DB container.
    hash_clave = subprocess.run(
        ["docker", "exec", "midnight-lace-backend-1",
         "python3", "-c",
         "from app.core.security import hash_password; print(hash_password('Admin123!'))"],
        capture_output=True, text=True
    ).stdout.strip()

    assert hash_clave.startswith("$2"), f"hash inválido: {hash_clave}"

    # Insertar persona + empleado (fechaActualizacionFotoDni NOT NULL sin default DB)
    db_run(
        f"INSERT INTO personas (documento, nombre, apellido, email, \"nombreUsuario\", "
        f"direccion, altura, localidad, ciudad, estado, \"urlFotoDocFrente\", \"urlFotoDocDorso\", "
        f"\"hashContrasenia\", \"fechaActualizacionFotoDni\") VALUES "
        f"('99999999', 'Admin', 'Test', '{email}', '{nick}', "
        f"'', '', '', '', 'activo', 'n/a', 'n/a', '{hash_clave}', CURRENT_DATE);"
    )
    persona_id = db_query(f"SELECT identificador FROM personas WHERE email='{email}'")
    db_run(f"INSERT INTO empleados (identificador) VALUES ({persona_id});")

    r = c.post("/v1/auth/login", json={"email": email, "clave": "Admin123!"})
    assert r.status_code == 200, f"login empleado falló: {r.text}"
    return r.json()["tokenAcceso"]


@pytest.fixture(scope="session")
def token_comprador(c):
    """Login comprador existente (aprobado@test.com)."""
    r = c.post("/v1/auth/login", json={"email": "aprobado@test.com", "clave": "Test123!"})
    assert r.status_code == 200
    return r.json()["tokenAcceso"]


class TestAdminAuth:
    def test_sin_token_401(self, c):
        r = c.get("/v1/admin/clientes")
        assert r.status_code == 401

    def test_comprador_403(self, c, token_comprador):
        r = c.get("/v1/admin/clientes", headers=auth(token_comprador))
        assert r.status_code == 403

    def test_comprador_multas_403(self, c, token_comprador):
        r = c.get("/v1/admin/multas", headers=auth(token_comprador))
        assert r.status_code == 403

    def test_comprador_crear_subastador_403(self, c, token_comprador):
        r = c.post("/v1/admin/subastadores", headers=auth(token_comprador),
                   json={"documento": "x", "nombre": "x", "apellido": "x",
                         "email": "x@x.com", "nombreUsuario": "x", "clave": "Abc12345"})
        assert r.status_code == 403


class TestListarClientes:
    def test_lista_ok(self, c, token_empleado):
        r = c.get("/v1/admin/clientes", headers=auth(token_empleado))
        assert r.status_code == 200
        data = r.json()
        assert "datos" in data
        assert "meta" in data

    def test_filtro_admitido_si(self, c, token_empleado):
        r = c.get("/v1/admin/clientes?admitido=si", headers=auth(token_empleado))
        assert r.status_code == 200
        for cliente in r.json()["datos"]:
            assert cliente["admitido"] == "si"

    def test_filtro_admitido_no(self, c, token_empleado):
        r = c.get("/v1/admin/clientes?admitido=no", headers=auth(token_empleado))
        assert r.status_code == 200

    def test_filtro_categoria(self, c, token_empleado):
        r = c.get("/v1/admin/clientes?categoria=comun", headers=auth(token_empleado))
        assert r.status_code == 200
        for cliente in r.json()["datos"]:
            assert cliente["categoria"] == "comun"

    def test_paginacion(self, c, token_empleado):
        r = c.get("/v1/admin/clientes?pagina=1&cantidad=1", headers=auth(token_empleado))
        assert r.status_code == 200
        assert len(r.json()["datos"]) <= 1
        assert "totalPaginas" in r.json()["meta"]

    def test_filtro_admitido_invalido_422(self, c, token_empleado):
        r = c.get("/v1/admin/clientes?admitido=maybe", headers=auth(token_empleado))
        assert r.status_code == 422

    def test_pagina_invalida_422(self, c, token_empleado):
        r = c.get("/v1/admin/clientes?pagina=0", headers=auth(token_empleado))
        assert r.status_code == 422


class TestVerCliente:
    def test_ver_cliente_existente(self, c, token_empleado):
        # Cliente ID 4 = aprobado@test.com
        r = c.get("/v1/admin/clientes/4", headers=auth(token_empleado))
        assert r.status_code == 200
        data = r.json()
        assert data["identificador"] == 4
        assert "nombre" in data
        assert "admitido" in data
        assert "multas" in data
        assert isinstance(data["multas"], list)

    def test_ver_cliente_no_encontrado(self, c, token_empleado):
        r = c.get("/v1/admin/clientes/999999", headers=auth(token_empleado))
        assert r.status_code == 404
        assert r.json()["codigo"] == "NO_ENCONTRADO"

    def test_ver_cliente_incluye_email(self, c, token_empleado):
        r = c.get("/v1/admin/clientes/4", headers=auth(token_empleado))
        assert r.status_code == 200
        assert r.json()["email"] == "aprobado@test.com"


class TestActualizarCliente:
    def test_patch_categoria(self, c, token_empleado):
        r = c.patch("/v1/admin/clientes/4", headers=auth(token_empleado),
                    json={"categoria": "especial"})
        assert r.status_code == 200
        assert r.json()["categoria"] == "especial"

    def test_patch_admitido(self, c, token_empleado):
        r = c.patch("/v1/admin/clientes/4", headers=auth(token_empleado),
                    json={"admitido": "si"})
        assert r.status_code == 200
        assert r.json()["admitido"] == "si"

    def test_patch_categoria_invalida_422(self, c, token_empleado):
        r = c.patch("/v1/admin/clientes/4", headers=auth(token_empleado),
                    json={"categoria": "vip"})
        assert r.status_code == 422

    def test_patch_sin_campos_422(self, c, token_empleado):
        r = c.patch("/v1/admin/clientes/4", headers=auth(token_empleado),
                    json={})
        assert r.status_code == 422

    def test_patch_cliente_no_encontrado(self, c, token_empleado):
        r = c.patch("/v1/admin/clientes/999999", headers=auth(token_empleado),
                    json={"categoria": "comun"})
        assert r.status_code == 404

    def test_patch_restaurar_categoria(self, c, token_empleado):
        r = c.patch("/v1/admin/clientes/4", headers=auth(token_empleado),
                    json={"categoria": "comun"})
        assert r.status_code == 200
        assert r.json()["categoria"] == "comun"


class TestListarMultas:
    def test_listar_todas(self, c, token_empleado):
        r = c.get("/v1/admin/multas", headers=auth(token_empleado))
        assert r.status_code == 200
        data = r.json()
        assert "datos" in data
        assert "meta" in data

    def test_filtro_pagada_si(self, c, token_empleado):
        r = c.get("/v1/admin/multas?pagada=si", headers=auth(token_empleado))
        assert r.status_code == 200
        for m in r.json()["datos"]:
            assert m["pagada"] == "si"

    def test_filtro_pagada_no(self, c, token_empleado):
        r = c.get("/v1/admin/multas?pagada=no", headers=auth(token_empleado))
        assert r.status_code == 200
        for m in r.json()["datos"]:
            assert m["pagada"] == "no"

    def test_filtro_invalido_422(self, c, token_empleado):
        r = c.get("/v1/admin/multas?pagada=maybe", headers=auth(token_empleado))
        assert r.status_code == 422


class TestCrearSubastador:
    def test_crear_ok(self, c, token_empleado):
        ts = int(time.time())
        r = c.post("/v1/admin/subastadores", headers=auth(token_empleado),
                   json={
                       "documento": f"8{ts}"[:10],
                       "nombre": "Nuevo",
                       "apellido": "Subastador",
                       "email": f"sub_{ts}@test.com",
                       "nombreUsuario": f"nsub_{ts}"[:30],
                       "clave": "SubClave123!",
                       "matricula": "ML-999",
                       "region": "Córdoba",
                   })
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["estado"] == "activo"
        assert "identificador" in data

    def test_crear_y_puede_loguear(self, c, token_empleado):
        ts = int(time.time()) + 1
        email = f"sub2_{ts}@test.com"
        r = c.post("/v1/admin/subastadores", headers=auth(token_empleado),
                   json={
                       "documento": f"9{ts}"[:10],
                       "nombre": "Sub",
                       "apellido": "Login",
                       "email": email,
                       "nombreUsuario": f"sl_{ts}"[:30],
                       "clave": "LoginSub123!",
                   })
        assert r.status_code == 201

        r2 = c.post("/v1/auth/login", json={"email": email, "clave": "LoginSub123!"})
        assert r2.status_code == 200, f"login falló: {r2.text}"
        assert "tokenAcceso" in r2.json()

    def test_clave_corta_422(self, c, token_empleado):
        r = c.post("/v1/admin/subastadores", headers=auth(token_empleado),
                   json={
                       "documento": "12345678",
                       "nombre": "A",
                       "apellido": "B",
                       "email": "short@test.com",
                       "nombreUsuario": "shortpass",
                       "clave": "abc123",
                   })
        assert r.status_code == 422

    def test_email_duplicado_500_o_422(self, c, token_empleado):
        """Email ya existente → DB unique constraint."""
        r = c.post("/v1/admin/subastadores", headers=auth(token_empleado),
                   json={
                       "documento": "11111110",
                       "nombre": "Dup",
                       "apellido": "Email",
                       "email": "subastador@midnightlace.com",
                       "nombreUsuario": "dup_email_user",
                       "clave": "DupEmail123!",
                   })
        assert r.status_code in (400, 409, 422, 500)
