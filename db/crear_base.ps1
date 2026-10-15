# ==============================================================================
# Crea la base 'monitoreo_red', aplica db/schema.sql y el usuario de aplicación
# definido en .env (TT-2027-A183)
# ==============================================================================
# Uso (desde la raíz del proyecto):
#   powershell -ExecutionPolicy Bypass -File db\crear_base.ps1
#
# Pide una vez la contraseña del usuario 'postgres' que definiste al instalar.
# Puede ejecutarse varias veces: no borra datos existentes.
# ==============================================================================

param(
    [string]$Usuario = "postgres",
    [string]$Servidor = "localhost",
    [int]$Puerto = 5432,
    [string]$Base = "monitoreo_red"
)

$ErrorActionPreference = "Stop"

# Acentos correctos en la salida de psql dentro de la consola de Windows.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PGCLIENTENCODING = "UTF8"

# Localiza psql: primero en el PATH, luego en la ruta del instalador oficial.
$psql = (Get-Command psql -ErrorAction SilentlyContinue).Source
if (-not $psql) {
    $psql = "C:\Program Files\PostgreSQL\17\bin\psql.exe"
}
if (-not (Test-Path $psql)) {
    Write-Error "No se encontró psql. Verifica que PostgreSQL 17 esté instalado."
}

# Pide la contraseña una sola vez y la deja solo en el entorno de este proceso.
if (-not $env:PGPASSWORD) {
    $segura = Read-Host "Contraseña del usuario '$Usuario'" -AsSecureString
    $env:PGPASSWORD = [System.Net.NetworkCredential]::new("", $segura).Password
}

$esquema = Join-Path $PSScriptRoot "schema.sql"
$conexion = @("-U", $Usuario, "-h", $Servidor, "-p", $Puerto, "-v", "ON_ERROR_STOP=1")

Write-Host "[1/3] Verificando la base '$Base'..."
$existe = & $psql @conexion -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$Base'"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

if ($existe -eq "1") {
    Write-Host "      La base ya existe; se conserva."
} else {
    & $psql @conexion -d postgres -c "CREATE DATABASE $Base ENCODING 'UTF8' TEMPLATE template0"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "      Base creada."
}

Write-Host "[2/3] Aplicando el esquema..."
& $psql @conexion -d $Base -f $esquema
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/3] Configurando el usuario de aplicación..."
$archivoEnv = Join-Path (Split-Path $PSScriptRoot -Parent) ".env"
if (-not (Test-Path $archivoEnv)) {
    Write-Error "No se encontró .env. Copia .env.example como .env y define MONITOREO_DB_PASSWORD."
}
$config = @{}
foreach ($linea in Get-Content $archivoEnv -Encoding UTF8) {
    if ($linea -match '^\s*([A-Z_]+)\s*=\s*(.*?)\s*$') { $config[$Matches[1]] = $Matches[2] }
}
& $psql @conexion -d $Base `
    -v "app_user=$($config['MONITOREO_DB_USER'])" `
    -v "app_password=$($config['MONITOREO_DB_PASSWORD'])" `
    -f (Join-Path $PSScriptRoot "permisos.sql")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Tablas en '$Base':"
& $psql @conexion -d $Base -c "\dt"
