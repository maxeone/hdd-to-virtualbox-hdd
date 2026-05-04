param(
    [Parameter(Mandatory = $true)]
    [int]$DiskNumber,

    [Parameter(Mandatory = $true)]
    [string[]]$PartitionNumbers,

    [Parameter(Mandatory = $true)]
    [string]$OutputPath,

    [string]$ToolsDir = (Join-Path (Split-Path $PSScriptRoot -Parent) "tools"),

    [switch]$ForceOverwrite
)

$ErrorActionPreference = "Stop"
$assignedLetters = @()

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

    throw "No encuentro una letra libre para montar temporalmente una particion."
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

if (-not (Test-IsAdministrator)) {
    throw "Este script necesita ejecutarse como Administrador."
}

if (-not $PartitionNumbers -or $PartitionNumbers.Count -eq 0) {
    throw "Debes indicar al menos una particion."
}

$PartitionNumbers = @(
    $PartitionNumbers |
        ForEach-Object { $_ -split "," } |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ } |
        ForEach-Object {
            $value = 0
            if (-not [int]::TryParse($_, [ref]$value)) {
                throw "El valor de particion '$_' no es valido."
            }
            $value
        }
) | Sort-Object -Unique

if (-not $PartitionNumbers -or $PartitionNumbers.Count -eq 0) {
    throw "Debes indicar al menos una particion valida."
}

$disk = Get-Disk -Number $DiskNumber -ErrorAction SilentlyContinue
if (-not $disk) {
    throw "No encuentro el disco $DiskNumber."
}

$resolvedOutputPath = [System.IO.Path]::GetFullPath($OutputPath)
$extension = [System.IO.Path]::GetExtension($resolvedOutputPath)
if (-not $extension) {
    $resolvedOutputPath = "$resolvedOutputPath.vhd"
    $extension = ".vhd"
}

if ($extension -notin @(".vhd", ".vhdx")) {
    throw "La salida debe terminar en .vhd o .vhdx."
}

$outputDir = Split-Path -Parent $resolvedOutputPath
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

$outputRoot = [System.IO.Path]::GetPathRoot($resolvedOutputPath)
if ($outputRoot -match '^[A-Za-z]:\\?$') {
    $outputDriveLetter = $outputRoot.Substring(0, 1)
    $outputPartition = Get-Partition -DriveLetter $outputDriveLetter -ErrorAction SilentlyContinue
    if ($outputPartition -and $outputPartition.DiskNumber -eq $DiskNumber) {
        throw "La carpeta de salida esta en el mismo disco origen. Elige una carpeta en otro disco para evitar errores al capturar la imagen."
    }
}

if ((Test-Path $resolvedOutputPath) -and -not $ForceOverwrite) {
    throw "El archivo de salida ya existe. Activa ForceOverwrite o cambia la ruta."
}

if ((Test-Path $resolvedOutputPath) -and $ForceOverwrite) {
    Remove-Item -LiteralPath $resolvedOutputPath -Force
}

$disk2vhdDir = Join-Path $ToolsDir "Disk2vhd"
$zipPath = Join-Path $ToolsDir "Disk2vhd.zip"
$exePath = Join-Path $disk2vhdDir "disk2vhd64.exe"

if (-not (Test-Path $exePath)) {
    New-Item -ItemType Directory -Path $ToolsDir -Force | Out-Null
    Write-Host "Descargando Disk2vhd..."
    Invoke-WebRequest -Uri "https://download.sysinternals.com/files/Disk2vhd.zip" -OutFile $zipPath
    Expand-Archive -LiteralPath $zipPath -DestinationPath $disk2vhdDir -Force
}

$sourceVolumes = @()
$estimatedUsedBytes = 0L
foreach ($partitionNumber in ($PartitionNumbers | Sort-Object -Unique)) {
    $partition = Get-Partition -DiskNumber $DiskNumber -PartitionNumber $partitionNumber -ErrorAction SilentlyContinue
    if (-not $partition) {
        throw "No encuentro la particion $partitionNumber en el disco $DiskNumber."
    }

    $mountPath = Ensure-DriveLetter -DiskNumber $DiskNumber -PartitionNumber $partitionNumber
    $sourceVolumes += $mountPath

    try {
        $driveLetter = $mountPath.Substring(0, 1)
        $volume = Get-Volume -DriveLetter $driveLetter -ErrorAction SilentlyContinue
        if ($volume -and $null -ne $volume.Size -and $null -ne $volume.SizeRemaining) {
            $usedBytes = [int64]$volume.Size - [int64]$volume.SizeRemaining
            if ($usedBytes -gt 0) {
                $estimatedUsedBytes += $usedBytes
            }
        }
    }
    catch {
    }
}

Write-Host "Creando imagen desde el disco $DiskNumber"
Write-Host "Particiones seleccionadas: $($PartitionNumbers -join ', ')"
Write-Host "Volumenes usados: $($sourceVolumes -join ', ')"
Write-Host "Salida: $resolvedOutputPath"
if ($estimatedUsedBytes -gt 0) {
    $estimatedUsedGB = [math]::Round($estimatedUsedBytes / 1GB, 2)
    Write-Host ("Estimado a copiar: {0} GB" -f $estimatedUsedGB)
}

try {
    $arguments = @("/accepteula") + $sourceVolumes + @($resolvedOutputPath)
    $process = Start-Process -FilePath $exePath -ArgumentList $arguments -PassThru -WindowStyle Hidden
    Write-Host ("Disk2vhd PID: {0}" -f $process.Id)

    $lastBytes = 0L
    $lastTime = Get-Date
    while (-not $process.HasExited) {
        Start-Sleep -Seconds 5
        if (Test-Path $resolvedOutputPath) {
            $file = Get-Item -LiteralPath $resolvedOutputPath
            $now = Get-Date
            $deltaBytes = $file.Length - $lastBytes
            $deltaSeconds = [math]::Max((New-TimeSpan -Start $lastTime -End $now).TotalSeconds, 1)
            $speedMBs = [math]::Round(($deltaBytes / 1MB) / $deltaSeconds, 1)
            $sizeGB = [math]::Round($file.Length / 1GB, 2)
            Write-Host ("  Tamano actual: {0} GB  Velocidad aprox.: {1} MB/s" -f $sizeGB, $speedMBs)
            $lastBytes = $file.Length
            $lastTime = $now
        }
        else {
            Write-Host "  Preparando snapshot VSS..."
        }
        $process.Refresh()
    }

    if (-not (Test-Path $resolvedOutputPath)) {
        throw "Disk2vhd termino con codigo $($process.ExitCode), pero no genero el archivo esperado."
    }

    $file = Get-Item -LiteralPath $resolvedOutputPath
    Write-Host "Imagen creada correctamente:"
    Write-Host ("  {0}" -f $file.FullName)
    Write-Host ("  Tamano: {0:N0} bytes" -f $file.Length)
}
finally {
    foreach ($item in $assignedLetters) {
        try {
            Remove-PartitionAccessPath -DiskNumber $item.DiskNumber -PartitionNumber $item.PartitionNumber -AccessPath "$($item.Letter):\"
        }
        catch {
        }
    }
}
