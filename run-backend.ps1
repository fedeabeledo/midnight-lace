<#
Run Midnight Lace backend with PostgreSQL in Docker.

Comandos que automatiza y que se usaron para validar:
  docker compose up -d
  backend\venv\Scripts\python.exe -m alembic upgrade head
  backend\venv\Scripts\python.exe -m scripts.seed
  backend\venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

Uso:
  .\run-backend.ps1
  .\run-backend.ps1 -Background
  .\run-backend.ps1 -Port 8010 -SkipInstall -NoSeed
#>

param(
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1",
    [switch]$Background,
    [switch]$SkipInstall,
    [switch]$NoSeed
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend = Join-Path $ProjectRoot "backend"
$Venv = Join-Path $Backend "venv"
$Python = Join-Path $Venv "Scripts\python.exe"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Assert-Command {
    param(
        [string]$Name,
        [string]$Help
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "No encontre '$Name'. $Help"
    }
}

function Invoke-External {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Step $Label
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo: $Label"
    }
}

function Test-DockerEngine {
    docker info *> $null
    return $LASTEXITCODE -eq 0
}

function Wait-DockerEngine {
    if (Test-DockerEngine) {
        Write-Host "Docker esta corriendo." -ForegroundColor Green
        return
    }

    $dockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (Test-Path -LiteralPath $dockerDesktop) {
        Write-Step "Iniciando Docker Desktop"
        Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    } else {
        throw "Docker Desktop no esta corriendo y no encontre el ejecutable en '$dockerDesktop'."
    }

    Write-Host "Esperando Docker Desktop..."
    for ($i = 1; $i -le 60; $i++) {
        Start-Sleep -Seconds 2
        if (Test-DockerEngine) {
            Write-Host "Docker esta corriendo." -ForegroundColor Green
            return
        }
    }

    throw "Docker Desktop no termino de arrancar. Abrilo manualmente y volve a ejecutar este script."
}

function Wait-Postgres {
    Write-Step "Esperando PostgreSQL"
    for ($i = 1; $i -le 45; $i++) {
        docker compose exec -T db pg_isready -U midnightlace -d midnightlace *> $null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL listo." -ForegroundColor Green
            return
        }
        Start-Sleep -Seconds 2
    }

    docker compose logs db --tail 50
    throw "PostgreSQL no respondio a tiempo."
}

function Ensure-Venv {
    if (Test-Path -LiteralPath $Python) {
        $venvVersion = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($venvVersion -ne "3.12") {
            throw "El entorno virtual existente usa Python $venvVersion. Borra '$Venv' y volve a ejecutar este script para crearlo con Python 3.12."
        }
        Write-Host "Venv listo: $Venv" -ForegroundColor Green
        return
    }

    Write-Step "Creando entorno virtual"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.12 --version *> $null
        if ($LASTEXITCODE -eq 0) {
            & py -3.12 -m venv $Venv
        } else {
            throw "No encontre Python 3.12 con el launcher 'py'. Instala Python 3.12."
        }
    } else {
        Assert-Command "python" "Instala Python 3.12 o superior."
        $pythonVersion = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($pythonVersion -ne "3.12") {
            throw "El comando 'python' apunta a Python $pythonVersion. Se necesita Python 3.12."
        }
        & python -m venv $Venv
    }

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $Python)) {
        throw "No pude crear el entorno virtual en '$Venv'."
    }
}

function Wait-Health {
    param([string]$Url)

    Write-Step "Verificando healthcheck"
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                Write-Host "$Url -> 200 OK" -ForegroundColor Green
                return
            }
        } catch {
            Start-Sleep -Seconds 1
        }
    }

    throw "El backend arranco, pero $Url no respondio a tiempo."
}

function Test-Health {
    param([string]$Url)

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Get-ListeningPid {
    param(
        [string]$Address,
        [int]$Port
    )

    $connection = Get-NetTCPConnection `
        -LocalAddress $Address `
        -LocalPort $Port `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($connection) {
        return $connection.OwningProcess
    }

    return $null
}

if (-not (Test-Path -LiteralPath $Backend)) {
    throw "No encontre la carpeta backend en '$Backend'."
}

Assert-Command "docker" "Instala Docker Desktop."

Set-Location $ProjectRoot

Wait-DockerEngine
Invoke-External "Levantando PostgreSQL con Docker Compose" { docker compose up -d db }
Wait-Postgres

$envExample = Join-Path $ProjectRoot ".env.example"
$envFile = Join-Path $Backend ".env"
if (-not (Test-Path -LiteralPath $envFile)) {
    Write-Step "Creando backend\.env"
    Copy-Item -LiteralPath $envExample -Destination $envFile
    Write-Host "Creado: $envFile" -ForegroundColor Green
}

New-Item -ItemType Directory -Force -Path (Join-Path $Backend "uploads") | Out-Null

Ensure-Venv

Set-Location $Backend

if (-not $SkipInstall) {
    Invoke-External "Instalando/validando dependencias Python" {
        & $Python -m pip install --disable-pip-version-check -r requirements.txt
    }
}

Invoke-External "Ejecutando migraciones Alembic" {
    & $Python -m alembic upgrade head
}

if (-not $NoSeed) {
    Invoke-External "Cargando seed inicial" {
        & $Python -m scripts.seed
    }
}

$BaseUrl = "http://$($BindHost):$Port"
$HealthUrl = "$BaseUrl/health"

Write-Host ""
Write-Host "Backend listo." -ForegroundColor Green
Write-Host "Docs:   $BaseUrl/docs"
Write-Host "Health: $HealthUrl"

if (Test-Health $HealthUrl) {
    Write-Host "Ya hay un backend respondiendo en $BaseUrl." -ForegroundColor Yellow
    return
}

$listeningPid = Get-ListeningPid -Address $BindHost -Port $Port
if ($listeningPid) {
    throw "El puerto $Port ya esta ocupado por el proceso PID $listeningPid. Cerra ese proceso o corre: .\run-backend.ps1 -Port 8010"
}

if ($Background) {
    $stdout = Join-Path $Backend "backend.out.log"
    $stderr = Join-Path $Backend "backend.err.log"

    Write-Step "Iniciando backend en segundo plano"
    $process = Start-Process `
        -FilePath $Python `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", $BindHost, "--port", "$Port") `
        -WorkingDirectory $Backend `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr `
        -WindowStyle Hidden `
        -PassThru

    Write-Host "PID: $($process.Id)"
    Write-Host "Logs: $stdout / $stderr"
    Wait-Health $HealthUrl
    return
}

Write-Step "Iniciando backend"
& $Python -m uvicorn app.main:app --reload --host $BindHost --port $Port
