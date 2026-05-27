#!/bin/bash
# Script de instalación automática para Fedora
# Ejecutar desde la raíz del proyecto: ./setup.sh

set -e  # Salir si hay error

echo "=== Instalación de Midnight Lace Backend ==="
echo ""

# Función para mensajes de error
error() {
    echo "✗ $1" >&2
    exit 1
}

# Función para mensajes de éxito
success() {
    echo "✓ $1"
}

# Función para mensajes de información
info() {
    echo "→ $1"
}

# Verificar Python
info "Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    error "Python no está instalado. Instalar con: sudo dnf install python3"
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oP 'Python \K[0-9]+\.[0-9]+')
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
    success "Python $PYTHON_VERSION detectado"
else
    error "Python $PYTHON_VERSION es muy viejo. Se necesita 3.10 o superior. Instalar con: sudo dnf install python3"
fi

# Verificar Docker
info "Verificando Docker..."
if ! command -v docker &> /dev/null; then
    error "Docker no está instalado. Instalar con: sudo dnf install docker docker-compose"
fi
success "Docker detectado"

# Verificar que Docker esté corriendo
info "Verificando que Docker esté corriendo..."
if ! docker info &> /dev/null; then
    error "Docker no está corriendo. Iniciar con: sudo systemctl start docker"
fi
success "Docker está corriendo"

# Verificar permisos de Docker
info "Verificando permisos de Docker..."
if ! docker ps &> /dev/null; then
    echo "⚠ El usuario actual no tiene permisos para Docker"
    echo "  Agregar usuario al grupo docker:"
    echo "    sudo usermod -aG docker \$USER"
    echo "  Luego cerrar sesión y volver a entrar"
    exit 1
fi
success "Permisos de Docker OK"

# Levantar PostgreSQL
echo ""
info "Levantando PostgreSQL con Docker..."
docker compose up -d || error "Error al levantar PostgreSQL"
success "PostgreSQL levantado"

# Esperar a que PostgreSQL esté listo
info "Esperando a que PostgreSQL esté listo..."
sleep 5

# Entrar al directorio backend
cd backend

# Crear entorno virtual
echo ""
info "Creando entorno virtual..."
$PYTHON_CMD -m venv venv || error "Error al crear entorno virtual"
success "Entorno virtual creado"

# Activar entorno virtual
info "Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo ""
info "Instalando dependencias..."
pip install -r requirements.txt || error "Error al instalar dependencias"
success "Dependencias instaladas"

# Copiar .env
echo ""
info "Configurando variables de entorno..."
if [ ! -f .env ]; then
    cp ../.env.example .env
    success "Archivo .env creado"
else
    success "Archivo .env ya existe"
fi

# Ejecutar migraciones
echo ""
info "Ejecutando migraciones de base de datos..."
alembic upgrade head || error "Error al ejecutar migraciones"
success "Migraciones ejecutadas"

# Ejecutar seed
echo ""
info "Cargando datos iniciales..."
python -m scripts.seed || error "Error al cargar datos iniciales"
success "Datos iniciales cargados"

# Mensaje final
echo ""
echo "=== Instalación completada ==="
echo ""
echo "Para iniciar el servidor, ejecutar:"
echo "  uvicorn app.main:app --reload --port 8000"
echo ""
echo "Luego abrir en el navegador:"
echo "  http://localhost:8000/docs"
echo ""
echo "Usuarios de prueba:"
echo "  Email: subastador@midnightlace.com"
echo "  Contraseña: sub123"
echo ""
