param(
    [Parameter(Mandatory = $true)]
    [string]$VhdPath,

    [Parameter(Mandatory = $true)]
    [string]$VmName,

    [string]$GuestOSType = "Windows7_64",

    [ValidateSet("BIOS", "UEFI")]
    [string]$FirmwareMode = "BIOS",

    [ValidateSet("IDE", "SATA")]
    [string]$StorageController = "IDE",

    [ValidateSet("PIIX3", "ICH9")]
    [string]$Chipset = "PIIX3",

    [int]$MemoryMB = 4096,
    [int]$CpuCount = 2,
    [switch]$DetachExistingHardDisks
)

$ErrorActionPreference = "Stop"

function Get-VBoxManagePath {
    $cmd = Get-Command VBoxManage -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $defaultPath = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
    if (Test-Path $defaultPath) {
        return $defaultPath
    }

    throw "No encuentro VBoxManage."
}

function Invoke-VBoxManage {
    param(
        [string[]]$Arguments
    )

    & $script:VBoxManagePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "VBoxManage fallo con codigo $LASTEXITCODE. Argumentos: $($Arguments -join ' ')"
    }
}

function Test-VMExists {
    param(
        [string]$VmName
    )

    $result = & $script:VBoxManagePath list vms
    return $result -match ('"{0}"' -f [regex]::Escape($VmName))
}

function Get-VMInfo {
    param(
        [string]$VmName
    )

    return & $script:VBoxManagePath showvminfo $VmName --machinereadable
}

function Ensure-StorageController {
    param(
        [string]$VmName,
        [string]$ControllerName,
        [string]$ControllerType
    )

    $info = Get-VMInfo -VmName $VmName
    if ($info -match ('storagecontrollername\d+="{0}"' -f [regex]::Escape($ControllerName))) {
        return
    }

    if ($ControllerType -eq "IDE") {
        Invoke-VBoxManage -Arguments @("storagectl", $VmName, "--name", $ControllerName, "--add", "ide", "--controller", "PIIX4")
        return
    }

    Invoke-VBoxManage -Arguments @("storagectl", $VmName, "--name", $ControllerName, "--add", "sata", "--controller", "IntelAhci")
}

function Detach-HardDisks {
    param(
        [string]$VmName
    )

    $info = Get-VMInfo -VmName $VmName
    foreach ($line in $info) {
        if ($line -match '^(IDE|SATA)-(\d+)-(\d+)="(.+)"$') {
            $controllerName = $matches[1]
            $port = $matches[2]
            $device = $matches[3]
            $medium = $matches[4]
            if ($medium -and $medium -ne "none" -and $medium -ne "emptydrive") {
                Invoke-VBoxManage -Arguments @("storageattach", $VmName, "--storagectl", $controllerName, "--port", $port, "--device", $device, "--medium", "none")
            }
        }
    }
}

$resolvedVhdPath = [System.IO.Path]::GetFullPath($VhdPath)
if (-not (Test-Path -LiteralPath $resolvedVhdPath)) {
    throw "No encuentro la imagen: $resolvedVhdPath"
}

$script:VBoxManagePath = Get-VBoxManagePath
$firmwareValue = if ($FirmwareMode -eq "UEFI") { "efi" } else { "bios" }
$controllerName = if ($StorageController -eq "IDE") { "IDE" } else { "SATA" }
$chipsetValue = $Chipset.ToLowerInvariant()

if (-not (Test-VMExists -VmName $VmName)) {
    Write-Host "Creando VM $VmName ..."
    Invoke-VBoxManage -Arguments @("createvm", "--name", $VmName, "--ostype", $GuestOSType, "--register")
}

Invoke-VBoxManage -Arguments @("modifyvm", $VmName, "--memory", $MemoryMB, "--cpus", $CpuCount, "--firmware", $firmwareValue, "--chipset", $chipsetValue, "--boot1", "disk", "--boot2", "dvd", "--boot3", "none", "--boot4", "none")
Ensure-StorageController -VmName $VmName -ControllerName $controllerName -ControllerType $StorageController

if ($DetachExistingHardDisks) {
    Detach-HardDisks -VmName $VmName
}

if ($StorageController -eq "IDE") {
    Invoke-VBoxManage -Arguments @("storageattach", $VmName, "--storagectl", $controllerName, "--port", "0", "--device", "0", "--type", "hdd", "--medium", $resolvedVhdPath)
}
else {
    Invoke-VBoxManage -Arguments @("storageattach", $VmName, "--storagectl", $controllerName, "--port", "0", "--device", "0", "--type", "hdd", "--medium", $resolvedVhdPath)
}

Write-Host "VM configurada correctamente."
Write-Host "  VM: $VmName"
Write-Host "  Disco: $resolvedVhdPath"
Write-Host "  Firmware: $FirmwareMode"
Write-Host "  Controlador: $StorageController"
