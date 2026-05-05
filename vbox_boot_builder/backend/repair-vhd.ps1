param(
    [Parameter(Mandatory = $true)]
    [string]$VhdPath,

    [ValidateSet("Auto", "BIOS", "UEFI")]
    [string]$FirmwareMode = "Auto",

    [int]$BootPartitionNumber = 0,
    [int]$WindowsPartitionNumber = 0,

    [switch]$ForceWindowsPartitionBoot,
    [switch]$SkipStorageDriverPatch,
    [switch]$SkipMountedDevicesReset,
    [switch]$RunChkdsk
)

$ErrorActionPreference = "Stop"
$assignedLetters = @()
$imageMounted = $false

function Test-IsAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-FreeDriveLetter {
    foreach ($letter in "R","S","T","U","V","W","X","Y","Z") {
        if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
            return $letter
        }
    }

    throw "No encuentro una letra libre para montar temporalmente el VHD."
}

function Ensure-DriveLetter {
    param(
        [int]$DiskNumber,
        [int]$PartitionNumber
    )

    $partition = Get-Partition -DiskNumber $DiskNumber -PartitionNumber $PartitionNumber
    if ($partition.DriveLetter) {
        return "$($partition.DriveLetter):"
    }

    $letter = Get-FreeDriveLetter
    Set-Partition -DiskNumber $DiskNumber -PartitionNumber $PartitionNumber -NewDriveLetter $letter
    $script:assignedLetters += [pscustomobject]@{
        DiskNumber = $DiskNumber
        PartitionNumber = $PartitionNumber
        Letter = $letter
    }

    return "${letter}:"
}

function Invoke-ChkdskIfRequested {
    param(
        [string]$DriveLetter
    )

    if (-not $RunChkdsk) {
        return
    }

    Write-Host "Comprobando $DriveLetter ..."
    try {
        & chkdsk.exe $DriveLetter /f /x
    }
    catch {
        Write-Warning "No pude ejecutar chkdsk sobre $DriveLetter. Sigo con la reparacion."
    }
}

function Get-WindowsPartition {
    param(
        [int]$DiskNumber,
        [System.Collections.IEnumerable]$Partitions
    )

    if ($WindowsPartitionNumber -gt 0) {
        return Get-Partition -DiskNumber $DiskNumber -PartitionNumber $WindowsPartitionNumber
    }

    foreach ($partition in ($Partitions | Sort-Object Size -Descending)) {
        if ($partition.Size -lt 5GB) {
            continue
        }

        $driveLetter = Ensure-DriveLetter -DiskNumber $DiskNumber -PartitionNumber $partition.PartitionNumber
        if (Test-Path "$driveLetter\Windows\System32\kernel32.dll") {
            return Get-Partition -DiskNumber $DiskNumber -PartitionNumber $partition.PartitionNumber
        }
    }

    throw "No pude localizar la particion que contiene Windows dentro del VHD."
}

function Get-BootPartition {
    param(
        [int]$DiskNumber,
        [System.Collections.IEnumerable]$Partitions,
        [Microsoft.Management.Infrastructure.CimInstance]$Disk,
        [Microsoft.Management.Infrastructure.CimInstance]$WindowsPartition
    )

    if ($ForceWindowsPartitionBoot) {
        return $WindowsPartition
    }

    if ($BootPartitionNumber -gt 0) {
        return Get-Partition -DiskNumber $DiskNumber -PartitionNumber $BootPartitionNumber
    }

    if ($FirmwareMode -eq "UEFI" -or ($FirmwareMode -eq "Auto" -and $Disk.PartitionStyle -eq "GPT")) {
        $candidates = $Partitions | Where-Object {
            $_.GptType -match "c12a7328" -or $_.Type -eq "System" -or $_.Size -lt 1GB
        }
        if ($candidates) {
            return $candidates | Sort-Object Size | Select-Object -First 1
        }
    }
    else {
        $candidates = $Partitions | Where-Object {
            $_.IsActive -or $_.Type -eq "System" -or $_.Size -lt 1GB
        }
        if ($candidates) {
            return $candidates | Sort-Object @{ Expression = "IsActive"; Descending = $true }, Size | Select-Object -First 1
        }
    }

    return $WindowsPartition
}

function Get-EffectiveFirmwareMode {
    param(
        [Microsoft.Management.Infrastructure.CimInstance]$Disk
    )

    if ($FirmwareMode -eq "UEFI" -and $Disk.PartitionStyle -ne "GPT") {
        Write-Warning "Se pidio UEFI sobre un disco MBR. Cambio automatico a BIOS."
        return "BIOS"
    }

    if ($FirmwareMode -eq "BIOS" -and $Disk.PartitionStyle -eq "GPT") {
        Write-Warning "Se pidio BIOS sobre un disco GPT. Cambio automatico a UEFI."
        return "UEFI"
    }

    if ($FirmwareMode -ne "Auto") {
        return $FirmwareMode
    }

    if ($Disk.PartitionStyle -eq "GPT") {
        return "UEFI"
    }

    return "BIOS"
}

function Repair-BiosBoot {
    param(
        [int]$DiskNumber,
        [System.Collections.IEnumerable]$Partitions,
        [string]$BootLetter,
        [string]$WindowsLetter,
        [int]$BootPartitionNumber
    )

    foreach ($partition in $Partitions) {
        $isActive = ($partition.PartitionNumber -eq $BootPartitionNumber)
        Set-Partition -DiskNumber $DiskNumber -PartitionNumber $partition.PartitionNumber -IsActive $isActive
    }

    Invoke-ChkdskIfRequested -DriveLetter $BootLetter
    Write-Host "Reescribiendo MBR y sector de arranque en $BootLetter ..."
    & bootsect.exe /nt60 $BootLetter /mbr /force
    if ($LASTEXITCODE -ne 0) {
        throw "bootsect fallo con codigo $LASTEXITCODE."
    }

    Write-Host "Regenerando BCD BIOS en $BootLetter ..."
    & bcdboot.exe "$WindowsLetter\Windows" /s $BootLetter /f BIOS /c /v
    if ($LASTEXITCODE -ne 0) {
        throw "bcdboot fallo con codigo $LASTEXITCODE."
    }
}

function Repair-BiosBootWithFallback {
    param(
        [int]$DiskNumber,
        [System.Collections.IEnumerable]$Partitions,
        [Microsoft.Management.Infrastructure.CimInstance]$BootPartition,
        [Microsoft.Management.Infrastructure.CimInstance]$WindowsPartition,
        [string]$BootLetter,
        [string]$WindowsLetter
    )

    $usedPartition = $null

    if ($BootPartition.PartitionNumber -ne $WindowsPartition.PartitionNumber) {
        try {
            Repair-BiosBoot `
                -DiskNumber $DiskNumber `
                -Partitions $Partitions `
                -BootLetter $BootLetter `
                -WindowsLetter $WindowsLetter `
                -BootPartitionNumber $BootPartition.PartitionNumber
            $usedPartition = $BootPartition
        }
        catch {
            Write-Host ""
            Write-Host "La particion de arranque dedicada no quedo utilizable. Cambio a arranque directo desde la particion de Windows."
            Write-Host "Motivo: $($_.Exception.Message)"
            Write-Host ""
        }
    }

    if (-not $usedPartition) {
        Repair-BiosBoot `
            -DiskNumber $DiskNumber `
            -Partitions $Partitions `
            -BootLetter $WindowsLetter `
            -WindowsLetter $WindowsLetter `
            -BootPartitionNumber $WindowsPartition.PartitionNumber
        $usedPartition = $WindowsPartition
    }

    return $usedPartition
}

function Repair-UefiBoot {
    param(
        [string]$BootLetter,
        [string]$WindowsLetter
    )

    Write-Host "Regenerando BCD UEFI en $BootLetter ..."
    & bcdboot.exe "$WindowsLetter\Windows" /s $BootLetter /f UEFI /c /v
    if ($LASTEXITCODE -ne 0) {
        throw "bcdboot fallo con codigo $LASTEXITCODE."
    }
}

function Enable-BootStorageDrivers {
    param(
        [string]$WindowsLetter
    )

    $hivePath = "$WindowsLetter\Windows\System32\config\SYSTEM"
    if (-not (Test-Path $hivePath)) {
        throw "No encuentro el hive SYSTEM en $hivePath"
    }

    $hiveName = "VHD_SYS_$PID"
    $hiveRoot = "HKLM\$hiveName"

    Write-Host "Activando drivers de almacenamiento para el primer arranque..."
    foreach ($staleHive in @("HKLM\VHD_SYS", $hiveRoot)) {
        & reg.exe unload $staleHive 2>$null | Out-Null
    }

    & reg.exe load $hiveRoot $hivePath 2>$null | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "No pude cargar el hive SYSTEM offline."
    }

    try {
        $controlSets = @("ControlSet001", "ControlSet002", "ControlSet003")
        $services = @(
            "atapi",
            "intelide",
            "pciide",
            "pciidex",
            "msahci",
            "storahci",
            "storport",
            "iaStorV",
            "iaStorA",
            "iaStorAV",
            "iaStorAVC",
            "iaStorAC",
            "iaStorVD",
            "stornvme",
            "nvme",
            "classpnp",
            "disk",
            "partmgr",
            "mountmgr",
            "volmgr",
            "volmgrx",
            "fltmgr",
            "fileinfo",
            "Ntfs",
            "crcdisk"
        )

        foreach ($controlSet in $controlSets) {
            foreach ($service in $services) {
                $servicePath = "$hiveRoot\$controlSet\Services\$service"
                & reg.exe query $servicePath 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    continue
                }

                & reg.exe add $servicePath /v Start /t REG_DWORD /d 0 /f 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  $controlSet\Services\$service -> Start=0"
                }

                $startOverridePath = "$servicePath\StartOverride"
                & reg.exe query $startOverridePath 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    foreach ($valueName in @("0", "1", "2", "3")) {
                        & reg.exe add $startOverridePath /v $valueName /t REG_DWORD /d 0 /f 2>$null | Out-Null
                    }
                }
            }
        }

        if (-not $SkipMountedDevicesReset) {
            Write-Host "Limpiando MountedDevices para forzar reenumeracion..."
            & reg.exe delete "$hiveRoot\MountedDevices" /va /f 2>$null | Out-Null
        }
    }
    finally {
        Start-Sleep -Milliseconds 300
        & reg.exe unload $hiveRoot 2>$null | Out-Host
    }
}

if (-not (Test-IsAdministrator)) {
    throw "Este script necesita ejecutarse como Administrador."
}

$resolvedVhdPath = [System.IO.Path]::GetFullPath($VhdPath)
if (-not (Test-Path -LiteralPath $resolvedVhdPath)) {
    throw "No encuentro el VHD: $resolvedVhdPath"
}

Write-Host "Montando imagen:"
Write-Host "  $resolvedVhdPath"

try {
    Mount-DiskImage -ImagePath $resolvedVhdPath -Access ReadWrite | Out-Null
    $imageMounted = $true
    Start-Sleep -Seconds 2

    $disk = Get-DiskImage -ImagePath $resolvedVhdPath | Get-Disk
    if (-not $disk) {
        throw "No pude obtener el disco montado desde la imagen."
    }

    $effectiveFirmware = Get-EffectiveFirmwareMode -Disk $disk
    $partitions = Get-Partition -DiskNumber $disk.Number | Sort-Object PartitionNumber
    if (-not $partitions) {
        throw "No encuentro particiones dentro de la imagen."
    }

    $windowsPartition = Get-WindowsPartition -DiskNumber $disk.Number -Partitions $partitions
    $bootPartition = Get-BootPartition -DiskNumber $disk.Number -Partitions $partitions -Disk $disk -WindowsPartition $windowsPartition

    $windowsLetter = Ensure-DriveLetter -DiskNumber $disk.Number -PartitionNumber $windowsPartition.PartitionNumber
    $bootLetter = Ensure-DriveLetter -DiskNumber $disk.Number -PartitionNumber $bootPartition.PartitionNumber

    Write-Host "Modo de firmware usado: $effectiveFirmware"
    Write-Host "Particion de arranque: $bootLetter (Partition $($bootPartition.PartitionNumber))"
    Write-Host "Particion de Windows:  $windowsLetter (Partition $($windowsPartition.PartitionNumber))"

    if ($effectiveFirmware -eq "UEFI") {
        Repair-UefiBoot -BootLetter $bootLetter -WindowsLetter $windowsLetter
    }
    else {
        $usedBootPartition = Repair-BiosBootWithFallback `
            -DiskNumber $disk.Number `
            -Partitions $partitions `
            -BootPartition $bootPartition `
            -WindowsPartition $windowsPartition `
            -BootLetter $bootLetter `
            -WindowsLetter $windowsLetter

        if ($usedBootPartition.PartitionNumber -ne $bootPartition.PartitionNumber) {
            $bootPartition = $usedBootPartition
            $bootLetter = Ensure-DriveLetter -DiskNumber $disk.Number -PartitionNumber $bootPartition.PartitionNumber
            Write-Host "Particion BIOS usada finalmente: $bootLetter (Partition $($bootPartition.PartitionNumber))"
        }
    }

    if (-not $SkipStorageDriverPatch) {
        Enable-BootStorageDrivers -WindowsLetter $windowsLetter
    }

    Write-Host ""
    Write-Host "Reparacion completada."
    Write-Host "Ya puedes usar la imagen en VirtualBox."
}
finally {
    foreach ($item in $assignedLetters) {
        try {
            Remove-PartitionAccessPath -DiskNumber $item.DiskNumber -PartitionNumber $item.PartitionNumber -AccessPath "$($item.Letter):\"
        }
        catch {
        }
    }

    if ($imageMounted) {
        try {
            Dismount-DiskImage -ImagePath $resolvedVhdPath
        }
        catch {
        }
    }
}
