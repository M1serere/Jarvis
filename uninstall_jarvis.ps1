[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$RemoveData
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$appName = "Jarvis"
$runKeyPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$startupApprovedPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
$defaultInstallDir = Join-Path ${env:ProgramFiles} $appName
$localDataDir = Join-Path ${env:LOCALAPPDATA} $appName
$desktopShortcut = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$startMenuShortcut = Join-Path (
    [Environment]::GetFolderPath("Programs")
) "$appName\$appName.lnk"
$scriptInstallDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $PSCommandPath }

function Write-Step {
    param([string]$Message)
    Write-Host "[Jarvis uninstall] $Message"
}

function Remove-RegistryValueIfExists {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $item = Get-ItemProperty -LiteralPath $Path -ErrorAction SilentlyContinue
    $property = $null
    if ($null -ne $item) {
        $property = $item.PSObject.Properties[$Name]
    }

    if ($null -ne $property) {
        if ($PSCmdlet.ShouldProcess("$Path\$Name", "Remove registry value")) {
            Remove-ItemProperty -LiteralPath $Path -Name $Name -ErrorAction SilentlyContinue
        }
    }
}

function Remove-FileIfExists {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (Test-Path -LiteralPath $Path) {
        if ($PSCmdlet.ShouldProcess($Path, "Remove file")) {
            Remove-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
        }
    }
}

function Remove-DirectoryIfExists {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (Test-Path -LiteralPath $Path) {
        if ($PSCmdlet.ShouldProcess($Path, "Remove directory")) {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Test-IsSubPath {
    param(
        [Parameter(Mandatory = $true)][string]$ParentPath,
        [Parameter(Mandatory = $true)][string]$ChildPath
    )

    try {
        $resolvedParent = [System.IO.Path]::GetFullPath($ParentPath).TrimEnd('\')
        $resolvedChild = [System.IO.Path]::GetFullPath($ChildPath).TrimEnd('\')
        return $resolvedChild.StartsWith($resolvedParent, [System.StringComparison]::OrdinalIgnoreCase)
    }
    catch {
        return $false
    }
}

function Find-BundledUninstaller {
    param([Parameter(Mandatory = $true)][string]$InstallDir)

    if (-not (Test-Path -LiteralPath $InstallDir)) {
        return $null
    }

    return Get-ChildItem -LiteralPath $InstallDir -Filter "unins*.exe" -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function Start-DelayedDirectoryRemoval {
    param([Parameter(Mandatory = $true)][string]$Path)

    $targetPath = [System.IO.Path]::GetFullPath($Path)
    if ([string]::IsNullOrWhiteSpace($targetPath) -or $targetPath.Length -lt 4) {
        throw "Refusing to remove suspicious path: '$Path'"
    }

    $tempScriptPath = Join-Path ([System.IO.Path]::GetTempPath()) ("jarvis_cleanup_{0}.ps1" -f ([guid]::NewGuid().ToString("N")))
    $cleanupScript = @"
Start-Sleep -Seconds 2
if (Test-Path -LiteralPath '$targetPath') {
    Remove-Item -LiteralPath '$targetPath' -Recurse -Force -ErrorAction SilentlyContinue
}
Remove-Item -LiteralPath '$tempScriptPath' -Force -ErrorAction SilentlyContinue
"@

    Set-Content -LiteralPath $tempScriptPath -Value $cleanupScript -Encoding UTF8
    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-WindowStyle", "Hidden",
        "-File", $tempScriptPath
    ) | Out-Null
}

function Get-UninstallEntry {
    $registryRoots = @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    )

    foreach ($root in $registryRoots) {
        if (-not (Test-Path -LiteralPath $root)) {
            continue
        }

        foreach ($subKey in Get-ChildItem -LiteralPath $root -ErrorAction SilentlyContinue) {
            $props = Get-ItemProperty -LiteralPath $subKey.PSPath -ErrorAction SilentlyContinue
            if ($null -eq $props) {
                continue
            }

            $displayNameProperty = $props.PSObject.Properties["DisplayName"]
            $installLocationProperty = $props.PSObject.Properties["InstallLocation"]
            $uninstallStringProperty = $props.PSObject.Properties["UninstallString"]

            $displayName = if ($null -ne $displayNameProperty) { [string]$displayNameProperty.Value } else { "" }
            $installLocation = if ($null -ne $installLocationProperty) { [string]$installLocationProperty.Value } else { "" }
            $uninstallString = if ($null -ne $uninstallStringProperty) { [string]$uninstallStringProperty.Value } else { "" }

            if (
                $displayName -eq $appName -or
                $installLocation -like "*\Jarvis" -or
                $uninstallString -like "*Jarvis*"
            ) {
                return [PSCustomObject]@{
                    DisplayName      = $displayName
                    InstallLocation  = $installLocation
                    UninstallString  = $uninstallString
                }
            }
        }
    }

    return $null
}

function Start-InnoUninstall {
    param([Parameter(Mandatory = $true)][string]$UninstallString)

    $trimmed = $UninstallString.Trim()
    if ([string]::IsNullOrWhiteSpace($trimmed)) {
        return $false
    }

    $exePath = $null
    if ($trimmed.StartsWith('"')) {
        $closingQuote = $trimmed.IndexOf('"', 1)
        if ($closingQuote -gt 1) {
            $exePath = $trimmed.Substring(1, $closingQuote - 1)
        }
    } else {
        $firstSpace = $trimmed.IndexOf(" ")
        if ($firstSpace -gt 0) {
            $exePath = $trimmed.Substring(0, $firstSpace)
        } else {
            $exePath = $trimmed
        }
    }

    if ([string]::IsNullOrWhiteSpace($exePath) -or -not (Test-Path -LiteralPath $exePath)) {
        return $false
    }

    if ($PSCmdlet.ShouldProcess($exePath, "Run bundled uninstaller")) {
        $existingArguments = $trimmed.Substring($trimmed.IndexOf($exePath) + $exePath.Length).Trim()
        $arguments = @()
        if (-not [string]::IsNullOrWhiteSpace($existingArguments)) {
            $arguments += $existingArguments
        }
        $arguments += @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
        $process = Start-Process -FilePath $exePath -ArgumentList $arguments -PassThru -Wait
        if ($process.ExitCode -ne 0) {
            throw "Bundled uninstaller exited with code $($process.ExitCode)."
        }
    }

    return $true
}

Write-Step "Stopping running processes."
Get-Process -Name $appName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Write-Step "Removing autostart registry entries."
Remove-RegistryValueIfExists -Path $runKeyPath -Name $appName
Remove-RegistryValueIfExists -Path $startupApprovedPath -Name $appName

$uninstallEntry = Get-UninstallEntry
$installDir = $defaultInstallDir
if ($null -ne $uninstallEntry -and -not [string]::IsNullOrWhiteSpace($uninstallEntry.InstallLocation)) {
    $installDir = $uninstallEntry.InstallLocation
}

Write-Step "Removing shortcuts."
Remove-FileIfExists -Path $desktopShortcut
Remove-FileIfExists -Path $startMenuShortcut
Remove-DirectoryIfExists -Path (Join-Path ([Environment]::GetFolderPath("Programs")) $appName)

$usedBundledUninstaller = $false
if ($null -ne $uninstallEntry -and -not [string]::IsNullOrWhiteSpace($uninstallEntry.UninstallString)) {
    Write-Step "Found installer entry in Windows registry."
    $usedBundledUninstaller = Start-InnoUninstall -UninstallString $uninstallEntry.UninstallString
}

if (-not $usedBundledUninstaller) {
    $bundledUninstaller = Find-BundledUninstaller -InstallDir $installDir
    if ($null -ne $bundledUninstaller) {
        Write-Step "Found bundled uninstaller in install directory."
        $usedBundledUninstaller = Start-InnoUninstall -UninstallString ('"{0}"' -f $bundledUninstaller.FullName)
    }
}

if (-not $usedBundledUninstaller) {
    Write-Step "Bundled uninstaller not found. Removing install directory manually."
    if (Test-IsSubPath -ParentPath $installDir -ChildPath $scriptInstallDir) {
        if ($PSCmdlet.ShouldProcess($installDir, "Schedule delayed directory removal")) {
            Write-Step "Current script is inside install directory. Scheduling delayed cleanup."
            Start-DelayedDirectoryRemoval -Path $installDir
        }
    } else {
        Remove-DirectoryIfExists -Path $installDir
    }
}

if ($RemoveData) {
    Write-Step "Removing local application data."
    Remove-DirectoryIfExists -Path $localDataDir
} else {
    Write-Step "Keeping user data in $localDataDir. Use -RemoveData to delete it too."
}

Write-Step "Uninstall completed."
