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

            $displayName = [string]$props.DisplayName
            $installLocation = [string]$props.InstallLocation
            $uninstallString = [string]$props.UninstallString

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
        $arguments = @("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART")
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
    Write-Step "Bundled uninstaller not found. Removing install directory manually."
    Remove-DirectoryIfExists -Path $installDir
}

if ($RemoveData) {
    Write-Step "Removing local application data."
    Remove-DirectoryIfExists -Path $localDataDir
} else {
    Write-Step "Keeping user data in $localDataDir. Use -RemoveData to delete it too."
}

Write-Step "Uninstall completed."
