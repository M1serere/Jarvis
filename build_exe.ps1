param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildAssetsDir = Join-Path $ProjectRoot "build_assets"
$DistDir = Join-Path $ProjectRoot "dist"
$InstallerScriptPath = Join-Path $ProjectRoot "JarvisSetup.iss"
$InstallerOutputPath = $null
$RootExePath = Join-Path $DistDir "Jarvis.exe"
$AppExePath = Join-Path $DistDir "Jarvis\\Jarvis.exe"
$VersionFilePath = Join-Path $ProjectRoot "version.txt"
$VersionInfoPath = Join-Path $BuildAssetsDir "jarvis_version_info.txt"
$LegacyInstallerOutputPath = Join-Path $ProjectRoot "Output\\JarvisSetup.exe"
$LegacyInstallerOutputDir = Join-Path $ProjectRoot "installer\\Output"
$IconPath = Join-Path $BuildAssetsDir "jarvis.ico"
$WizardImagePath = Join-Path $BuildAssetsDir "wizard.bmp"
$WizardSmallImagePath = Join-Path $BuildAssetsDir "wizard-small.bmp"
$LogoPath = Join-Path $ProjectRoot "j_logo.png"
$SpecPath = Join-Path $ProjectRoot "jarvis.spec"
$VenvPython = Join-Path $ProjectRoot ".venv\\Scripts\\python.exe"

function Get-PythonExe {
    if (Test-Path $VenvPython) {
        return $VenvPython
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    throw "Python not found. Install Python or create .venv first."
}

function Test-TkinterAvailable {
    param(
        [string]$PythonExe
    )

    $tkCheckScript = @'
import os
import sys
import tkinter
import _tkinter

tcl_root = os.path.join(sys.base_prefix, "tcl")

if not os.path.isdir(tcl_root):
    raise SystemExit("Tcl root not found: " + tcl_root)

tcl_dirs = [
    d for d in os.listdir(tcl_root)
    if d.lower().startswith("tcl") and os.path.isdir(os.path.join(tcl_root, d))
]
tk_dirs = [
    d for d in os.listdir(tcl_root)
    if d.lower().startswith("tk") and os.path.isdir(os.path.join(tcl_root, d))
]

if not tcl_dirs:
    raise SystemExit("Tcl data dir not found inside: " + tcl_root)

if not tk_dirs:
    raise SystemExit("Tk data dir not found inside: " + tcl_root)

tcl_dir = os.path.join(tcl_root, sorted(tcl_dirs)[-1])
tk_dir  = os.path.join(tcl_root, sorted(tk_dirs)[-1])

missing = [path for path in (tcl_dir, tk_dir) if not os.path.isdir(path)]
if missing:
    raise SystemExit("Missing Tcl/Tk runtime directories: " + ", ".join(missing))

print("TK_OK", tkinter.TkVersion, tcl_dir, tk_dir)
'@

    $tkCheckPath = Join-Path $ProjectRoot ".tk_check.py"
    Set-Content -Path $tkCheckPath -Value $tkCheckScript -Encoding UTF8

    try {
        & $PythonExe $tkCheckPath
    }
    finally {
        Remove-Item -LiteralPath $tkCheckPath -Force -ErrorAction SilentlyContinue
    }

    if ($LASTEXITCODE -ne 0) {
        throw @'
The Python used for the build does not have working Tcl/Tk runtime data.
Because of that, the packaged exe can fail with errors like:
- No module named tkinter
- Tcl data directory "_tcl_data" not found
- Tk data directory "_tk_data" not found

What to do:
1. Install the regular Python from python.org, not a trimmed-down distribution.
2. Check that these directories exist:
   - <Python>\tcl\tcl8.6
   - <Python>\tcl\tk8.6
3. Recreate .venv with that Python.
4. Run the build again.
'@
    }
}

function Ensure-BuildAssets {
    if (-not (Test-Path $LogoPath)) {
        throw "Logo file not found: $LogoPath"
    }

    if (-not (Test-Path $BuildAssetsDir)) {
        New-Item -ItemType Directory -Path $BuildAssetsDir | Out-Null
    }

    Add-Type -AssemblyName System.Drawing

    $bitmap = [System.Drawing.Bitmap]::FromFile($LogoPath)
    try {
        $iconBitmap = New-Object System.Drawing.Bitmap 256, 256
        $iconGraphics = [System.Drawing.Graphics]::FromImage($iconBitmap)
        try {
            $iconGraphics.Clear([System.Drawing.Color]::Transparent)
            $iconGraphics.DrawImage($bitmap, 0, 0, 256, 256)
        }
        finally {
            $iconGraphics.Dispose()
        }

        $pngStream = New-Object System.IO.MemoryStream
        try {
            $iconBitmap.Save($pngStream, [System.Drawing.Imaging.ImageFormat]::Png)
            $pngBytes = $pngStream.ToArray()
        }
        finally {
            $pngStream.Dispose()
            $iconBitmap.Dispose()
        }

        $fileStream = [System.IO.File]::Open($IconPath, [System.IO.FileMode]::Create)
        $writer = New-Object System.IO.BinaryWriter($fileStream)
        try {
            $writer.Write([UInt16]0)
            $writer.Write([UInt16]1)
            $writer.Write([UInt16]1)
            $writer.Write([Byte]0)
            $writer.Write([Byte]0)
            $writer.Write([Byte]0)
            $writer.Write([Byte]0)
            $writer.Write([UInt16]1)
            $writer.Write([UInt16]32)
            $writer.Write([UInt32]$pngBytes.Length)
            $writer.Write([UInt32]22)
            $writer.Write($pngBytes)
        }
        finally {
            $writer.Dispose()
            $fileStream.Dispose()
        }

        $wizardBitmap = New-Object System.Drawing.Bitmap 164, 314
        $wizardGraphics = [System.Drawing.Graphics]::FromImage($wizardBitmap)
        try {
            $wizardGraphics.Clear([System.Drawing.Color]::FromArgb(3, 19, 31))
            $wizardGraphics.DrawImage($bitmap, 10, 85, 144, 144)
        }
        finally {
            $wizardGraphics.Dispose()
        }
        $wizardBitmap.Save($WizardImagePath, [System.Drawing.Imaging.ImageFormat]::Bmp)
        $wizardBitmap.Dispose()

        $smallBitmap = New-Object System.Drawing.Bitmap 55, 55
        $smallGraphics = [System.Drawing.Graphics]::FromImage($smallBitmap)
        try {
            $smallGraphics.Clear([System.Drawing.Color]::FromArgb(7, 31, 51))
            $smallGraphics.DrawImage($bitmap, 4, 4, 47, 47)
        }
        finally {
            $smallGraphics.Dispose()
        }
        $smallBitmap.Save($WizardSmallImagePath, [System.Drawing.Imaging.ImageFormat]::Bmp)
        $smallBitmap.Dispose()
    }
    finally {
        $bitmap.Dispose()
    }
}

function Get-AppVersion {
    if (-not (Test-Path $VersionFilePath)) {
        throw "Version file not found: $VersionFilePath"
    }

    $version = (Get-Content -Path $VersionFilePath -Raw).Trim()
    if ($version -notmatch '^\d+\.\d+\.\d+(\.\d+)?$') {
        throw "Invalid version '$version'. Use format major.minor.patch or major.minor.patch.build."
    }

    return $version
}

function Get-WindowsVersion {
    param(
        [string]$Version
    )

    $parts = $Version.Split('.')
    while ($parts.Count -lt 4) {
        $parts += "0"
    }

    return ($parts -join '.')
}

function Update-VersionInfoFile {
    param(
        [string]$AppVersion
    )

    if (-not (Test-Path $BuildAssetsDir)) {
        New-Item -ItemType Directory -Path $BuildAssetsDir | Out-Null
    }

    $windowsVersion = Get-WindowsVersion -Version $AppVersion
    $versionTuple = ($windowsVersion.Split('.') | ForEach-Object { [int]$_ }) -join ', '
    $versionInfoContent = @"
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=($versionTuple),
    prodvers=($versionTuple),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('CompanyName', 'Jarvis'),
            StringStruct('FileDescription', 'Jarvis Voice Assistant'),
            StringStruct('FileVersion', '$windowsVersion'),
            StringStruct('InternalName', 'Jarvis'),
            StringStruct('OriginalFilename', 'Jarvis.exe'),
            StringStruct('ProductName', 'Jarvis'),
            StringStruct('ProductVersion', '$windowsVersion')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@

    Set-Content -Path $VersionInfoPath -Value $versionInfoContent -Encoding UTF8
}

function Remove-StaleBuildOutputs {
    $pathsToRemove = @(
        $InstallerOutputPath,
        $LegacyInstallerOutputPath,
        (Join-Path $LegacyInstallerOutputDir "JarvisSetup.exe"),
        (Join-Path $LegacyInstallerOutputDir "JarvisSetup_*.exe"),
        $RootExePath,
        $AppExePath,
        (Join-Path $ProjectRoot "dist"),
        (Join-Path $ProjectRoot "build"),
        (Join-Path $ProjectRoot "Output")
    )

    foreach ($path in $pathsToRemove) {
        Get-Item -LiteralPath $path -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.PSIsContainer) {
                Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
            else {
                Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
            }
        }

        Get-ChildItem -Path $path -ErrorAction SilentlyContinue | ForEach-Object {
            if ($_.PSIsContainer) {
                Remove-Item -LiteralPath $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            }
            else {
                Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
            }
        }
    }

    New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
    New-Item -ItemType Directory -Force -Path $LegacyInstallerOutputDir | Out-Null
}

function Invoke-PyInstallerBuild {
    param(
        [string]$AppVersion
    )

    $pythonExe = Get-PythonExe
    Test-TkinterAvailable -PythonExe $pythonExe
    Update-VersionInfoFile -AppVersion $AppVersion
    
    & $pythonExe -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
    & $pythonExe -m pip install pyinstaller
    & $pythonExe -m PyInstaller --noconfirm --clean $SpecPath
}

function Invoke-InnoSetupBuild {
    param(
        [string]$AppVersion
    )

    if (-not (Test-Path $InstallerScriptPath)) {
        throw "Installer script not found: $InstallerScriptPath"
    }

    $compilerCandidates = @(
        "${env:ProgramFiles(x86)}\\Inno Setup 6\\ISCC.exe",
        "${env:ProgramFiles}\\Inno Setup 6\\ISCC.exe",
        "${env:LocalAppData}\\Programs\\Inno Setup 6\\ISCC.exe"
    )

    $compilerPath = $compilerCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $compilerPath) {
        throw "Inno Setup compiler not found. Install Inno Setup 6 and rerun the script."
    }

    & $compilerPath "/DMyAppVersion=$AppVersion" $InstallerScriptPath
}

Ensure-BuildAssets
$appVersion = Get-AppVersion
$InstallerOutputPath = Join-Path $LegacyInstallerOutputDir ("JarvisSetup_{0}.exe" -f $appVersion)
Remove-StaleBuildOutputs
Invoke-PyInstallerBuild -AppVersion $appVersion

if ((Test-Path $RootExePath) -and (Test-Path $AppExePath)) {
    Remove-Item -LiteralPath $RootExePath -Force
}

if (-not $SkipInstaller) {
    Invoke-InnoSetupBuild -AppVersion $appVersion
}

Write-Host ""
Write-Host "Build finished."
Write-Host "App version: $appVersion"
Write-Host "App folder: $DistDir\\Jarvis"
Write-Host "App exe: $AppExePath"
Write-Host "Installer script: $InstallerScriptPath"
Write-Host "Installer output: $InstallerOutputPath"
