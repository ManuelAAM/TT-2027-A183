# Convierte los mockups HTML de esta carpeta a PNG con Microsoft Edge en modo headless.
#   powershell -ExecutionPolicy Bypass -File docs/mockups/render_mockups.ps1
$ErrorActionPreference = "Stop"
$edge = @("C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
          "C:\Program Files\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { throw "No se encontró Microsoft Edge." }
$perfil = Join-Path $env:TEMP "edge_mockups"
Get-ChildItem $PSScriptRoot -Filter "m*.html" | ForEach-Object {
    $png = [IO.Path]::ChangeExtension($_.FullName, ".png")
    & $edge --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$perfil" --force-device-scale-factor=1.5 `
        --window-size=1440,900 --screenshot="$png" ("file:///" + $_.FullName.Replace('\', '/')) 2>$null
    Start-Sleep -Milliseconds 1500
    "{0} -> {1}" -f $_.Name, (Split-Path $png -Leaf)
}
