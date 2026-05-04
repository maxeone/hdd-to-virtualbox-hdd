param()

$ErrorActionPreference = "Stop"

function Get-PartitionVolume {
    param(
        [Microsoft.Management.Infrastructure.CimInstance]$Partition
    )

    if ($Partition.DriveLetter) {
        return Get-Volume -DriveLetter $Partition.DriveLetter -ErrorAction SilentlyContinue
    }

    return $null
}

function Test-PartitionPath {
    param(
        [string]$DriveLetter,
        [string]$RelativePath
    )

    if (-not $DriveLetter) {
        return $false
    }

    return Test-Path -LiteralPath (Join-Path "$DriveLetter\" $RelativePath)
}

$disks = foreach ($disk in (Get-Disk | Sort-Object Number)) {
    $partitions = foreach ($partition in (Get-Partition -DiskNumber $disk.Number -ErrorAction SilentlyContinue | Sort-Object PartitionNumber)) {
        $volume = Get-PartitionVolume -Partition $partition
        $driveLetter = if ($partition.DriveLetter) { "$($partition.DriveLetter):" } else { $null }
        $hasWindows = Test-PartitionPath -DriveLetter $driveLetter -RelativePath "Windows\System32\kernel32.dll"
        $hasBootMgr = Test-PartitionPath -DriveLetter $driveLetter -RelativePath "bootmgr"
        $hasBootFolder = Test-PartitionPath -DriveLetter $driveLetter -RelativePath "Boot"
        $hasEfiBoot = Test-PartitionPath -DriveLetter $driveLetter -RelativePath "EFI\Microsoft\Boot"

        [pscustomobject]@{
            PartitionNumber = [int]$partition.PartitionNumber
            DriveLetter = $driveLetter
            Size = [uint64]$partition.Size
            Offset = [uint64]$partition.Offset
            Type = [string]$partition.Type
            MbrType = [string]$partition.MbrType
            GptType = [string]$partition.GptType
            IsActive = [bool]$partition.IsActive
            IsBoot = [bool]$partition.IsBoot
            IsSystem = [bool]$partition.IsSystem
            AccessPaths = @($partition.AccessPaths)
            FileSystem = if ($volume) { [string]$volume.FileSystem } else { $null }
            FileSystemLabel = if ($volume) { [string]$volume.FileSystemLabel } else { $null }
            HealthStatus = if ($volume) { [string]$volume.HealthStatus } else { $null }
            HasWindows = $hasWindows
            HasBootMgr = $hasBootMgr
            HasBootFolder = $hasBootFolder
            HasEfiBoot = $hasEfiBoot
        }
    }

    $suggestedWindows = $partitions |
        Where-Object HasWindows |
        Sort-Object Size -Descending |
        Select-Object -First 1

    $suggestedBoot = $null
    if ($disk.PartitionStyle -eq "GPT") {
        $suggestedBoot = $partitions |
            Where-Object { $_.HasEfiBoot -or $_.FileSystem -eq "FAT32" -or $_.GptType -match "c12a7328" } |
            Sort-Object Size |
            Select-Object -First 1
    }
    else {
        $suggestedBoot = $partitions |
            Where-Object { $_.IsActive -or $_.HasBootMgr -or $_.HasBootFolder } |
            Sort-Object @{ Expression = "IsActive"; Descending = $true }, Size |
            Select-Object -First 1
    }

    if (-not $suggestedBoot -and $suggestedWindows) {
        $suggestedBoot = $suggestedWindows
    }

    [pscustomobject]@{
        DiskNumber = [int]$disk.Number
        FriendlyName = [string]$disk.FriendlyName
        SerialNumber = [string]$disk.SerialNumber
        BusType = [string]$disk.BusType
        PartitionStyle = [string]$disk.PartitionStyle
        OperationalStatus = [string]$disk.OperationalStatus
        IsBoot = [bool]$disk.IsBoot
        IsSystem = [bool]$disk.IsSystem
        IsOffline = [bool]$disk.IsOffline
        Size = [uint64]$disk.Size
        SuggestedWindowsPartition = if ($suggestedWindows) { [int]$suggestedWindows.PartitionNumber } else { $null }
        SuggestedBootPartition = if ($suggestedBoot) { [int]$suggestedBoot.PartitionNumber } else { $null }
        Partitions = $partitions
    }
}

$disks | ConvertTo-Json -Depth 8
