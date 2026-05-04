param(
    [switch]$OneDir
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$appScript = Join-Path $root "vbox_boot_builder\virtualbox_boot_builder.py"
$backendDir = Join-Path $root "vbox_boot_builder\backend"
$distDir = Join-Path $root "portable\VirtualBoxBootBuilder"
$buildDir = Join-Path $root "build"
$name = "VirtualBoxBootBuilder"

if (-not (Test-Path $appScript)) {
    throw "No encuentro la app Python: $appScript"
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --uac-admin `
    --name $name `
    $(if (-not $OneDir) { "--onefile" }) `
    --add-data "$backendDir;backend" `
    --distpath $distDir `
    --workpath $buildDir `
    $appScript

Write-Host "Build completado."
if ($OneDir) {
    Write-Host "Salida: $(Join-Path $distDir $name)"
}
else {
    Write-Host "Salida: $(Join-Path $distDir "$name.exe")"
}
