# Cómo correr el proyecto localmente

La única dependencia es **Docker Desktop**.

- Windows/Mac: https://www.docker.com/products/docker-desktop/
- Linux: https://docs.docker.com/engine/install/

---

## Primera vez

```bash
docker compose up --build
```

Esto:
1. Descarga la imagen de PostgreSQL 16
2. Construye la imagen del backend (Python + dependencias)
3. Levanta la base de datos
4. Corre las migraciones automáticamente
5. Carga los datos iniciales (países, usuario empresa, subastador de prueba, depósitos, seguros)
6. Arranca el servidor en `http://localhost:8000`

La primera vez tarda unos minutos porque descarga las imágenes y construye el container.

---

## Las demás veces

```bash
docker compose up
```

---

## Verificar que funciona

Abrir en el navegador: http://localhost:8000/docs

Ahí está el Swagger con todos los endpoints. Para usarlos se necesita la API key (pedirla a Fede).

### Usuario de prueba

| Campo      | Valor                           |
|------------|---------------------------------|
| Email      | `subastador@midnightlace.com`   |
| Contraseña | `Subastador123!`                |
| Rol        | Subastador                      |

---

## Parar el servidor

```bash
# Para los containers pero mantiene los datos de la DB
docker compose down

# Para los containers Y borra la base de datos (reset completo)
docker compose down -v
```

---

## Reconstruir el backend

Si se agregan paquetes a `requirements.txt` o se hacen cambios en el `Dockerfile`:

```bash
docker compose up --build
```

Si solo se cambia código Python, alcanza con `docker compose up` (el código se refleja automáticamente porque se monta el directorio).

---

## Variables de entorno

Las variables sensibles **no van en `docker-compose.yml`** para no exponerlas en el repositorio. En cambio, Docker Compose las lee automáticamente desde un archivo `.env` en la raíz del proyecto (que está en `.gitignore` y nunca se sube).

### Setup inicial

```bash
cp .env.example .env
```

Luego editar `.env` con los valores reales. El archivo tiene tres variables:

| Variable | Descripción |
|---|---|
| `JWT_SECRET` | String largo y aleatorio para firmar los tokens. Puede ser cualquier cosa para desarrollo local. |
| `SMTP_USER` | Email de Gmail desde el que se mandan los correos. Opcional, ver abajo. |
| `SMTP_PASSWORD` | App Password de Gmail (no la contraseña normal). Opcional, ver abajo. |
| `API_KEY` | Si se deja vacío, todos los endpoints son accesibles sin API key (ideal para desarrollo local). |

> Las variables de DB ya están hardcodeadas en `docker-compose.yml` porque son fijas para el entorno local. No hace falta tocarlas.

### Configurar SMTP (opcional)

Necesario solo para probar los flows que mandan email (código de verificación al registrarse, etc.).

1. Ir a https://myaccount.google.com/apppasswords
2. Crear una app password para "Mail"
3. En `.env`:

```
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
```

Si no se configura, el resto del proyecto funciona igual, solo fallan los envíos de mail.

---

## Archivos subidos

Las fotos y archivos que se suben a través de la API se guardan en la carpeta `uploads/` en la raíz del proyecto. Esta carpeta se crea automáticamente y los archivos persisten aunque se reinicien los containers.

---

## Troubleshooting

**El puerto 5432 ya está en uso**
Hay una instancia de PostgreSQL corriendo en la máquina. Pararla o cambiar el puerto en `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # usar 5433 en vez de 5432
```

**El puerto 8000 ya está en uso**
Cambiar el puerto expuesto en `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # el server queda en localhost:8001
```

**`docker compose` no funciona, solo `docker-compose`**
Versión vieja de Docker. Actualizar Docker Desktop o usar `docker-compose` (con guión) en todos los comandos.

**Error en migraciones o seed al arrancar**
Probablemente la DB no terminó de inicializarse. Correr de nuevo:
```bash
docker compose down && docker compose up
```
