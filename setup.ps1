# Script de instalación automática para Windows
# Ejecutar en PowerShell desde la raíz del proyecto

Write-Host "=== Instalación de Midnight Lace Backend ===" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 3 -and $minor -ge 10) {
            Write-Host "✓ Python $major.$minor detectado" -ForegroundColor Green
        } else {
            Write-Host "✗ Python $major.$minor es muy viejo. Se necesita 3.10 o superior." -ForegroundColor Red
            Write-Host "Descargar desde: https://www.python.org/downloads/" -ForegroundColor Yellow
            exit 1
        }
    }
} catch {
    Write-Host "✗ Python no está instalado" -ForegroundColor Red
    Write-Host "Descargar desde: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Verificar Docker
Write-Host "Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✓ Docker detectado: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker no está instalado" -ForegroundColor Red
    Write-Host "Descargar desde: https://www.docker.com/products/docker-desktop/" -ForegroundColor Yellow
    exit 1
}

# Verificar que Docker esté corriendo
Write-Host "Verificando que Docker esté corriendo..." -ForegroundColor Yellow
try {
    docker info >$null 2>&1
    Write-Host "✓ Docker está corriendo" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker no está corriendo. Abrir Docker Desktop y esperar a que diga 'Engine running'" -ForegroundColor Red
    exit 1
}

# Levantar PostgreSQL
Write-Host ""
Write-Host "Levantando PostgreSQL con Docker..." -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al levantar PostgreSQL" -ForegroundColor Red
    exit 1
}
Write-Host "✓ PostgreSQL levantado" -ForegroundColor Green

# Esperar a que PostgreSQL esté listo
Write-Host "Esperando a que PostgreSQL esté listo..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Entrar al directorio backend
Set-Location backend

# Crear entorno virtual
Write-Host ""
Write-Host "Creando entorno virtual..." -ForegroundColor Cyan
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al crear entorno virtual" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Entorno virtual creado" -ForegroundColor Green

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
.\venv\Scripts\Activate.ps1

# Instalar dependencias
Write-Host ""
Write-Host "Instalando dependencias..." -ForegroundColor Cyan
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al instalar dependencias" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencias instaladas" -ForegroundColor Green

# Copiar .env
Write-Host ""
Write-Host "Configurando variables de entorno..." -ForegroundColor Cyan
if (!(Test-Path .env)) {
    Copy-Item ..\.env.example .env
    Write-Host "✓ Archivo .env creado" -ForegroundColor Green
} else {
    Write-Host "✓ Archivo .env ya existe" -ForegroundColor Green
}

# Ejecutar migraciones
Write-Host ""
Write-Host "Ejecutando migraciones de base de datos..." -ForegroundColor Cyan
alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al ejecutar migraciones" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Migraciones ejecutadas" -ForegroundColor Green

# Ejecutar seed
Write-Host ""
Write-Host "Cargando datos iniciales..." -ForegroundColor Cyan
python -m scripts.seed
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Error al cargar datos iniciales" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Datos iniciales cargados" -ForegroundColor Green

# Mensaje final
Write-Host ""
Write-Host "=== Instalación completada ===" -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar el servidor, ejecutar:" -ForegroundColor Cyan
Write-Host "  uvicorn app.main:app --reload --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "Luego abrir en el navegador:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "Usuarios de prueba:" -ForegroundColor Cyan
Write-Host "  Email: subastador@midnightlace.com" -ForegroundColor White
Write-Host "  Contraseña: sub123" -ForegroundColor White
Write-Host ""
