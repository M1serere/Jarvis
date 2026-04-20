param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BuildAssetsDir = Join-Path $ProjectRoot "build_assets"
$DistDir = Join-Path $ProjectRoot "dist"
$InstallerScriptPath = Join-Path $ProjectRoot "JarvisSetup.iss"
$InstallerOutputPath = Join-Path $ProjectRoot "JarvisSetup.exe"
$RootExePath = Join-Path $DistDir "Jarvis.exe"
$AppExePath = Join-Path $DistDir "Jarvis\\Jarvis.exe"
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

    & $PythonExe -c "import tkinter; import _tkinter; print('TK_OK', tkinter.TkVersion)"
    if ($LASTEXITCODE -ne 0) {
        throw @'
В Python, которым собирается проект, не найден tkinter.
Из-за этого установленный exe падает с ошибкой: No module named tkinter.

Что сделать:
1. Поставить обычный Python с python.org, а не урезанную сборку.
2. Убедиться, что установлен Tcl/Tk.
3. Пересоздать .venv и заново собрать проект.
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

function Invoke-PyInstallerBuild {
    $pythonExe = Get-PythonExe
    Test-TkinterAvailable -PythonExe $pythonExe
    
    & $pythonExe -m pip install -r (Join-Path $ProjectRoot "requirements.txt")
    & $pythonExe -m pip install pyinstaller
    & $pythonExe -m PyInstaller --noconfirm --clean $SpecPath
}

function Invoke-InnoSetupBuild {
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

    & $compilerPath $InstallerScriptPath
}

Ensure-BuildAssets
Invoke-PyInstallerBuild

if ((Test-Path $RootExePath) -and (Test-Path $AppExePath)) {
    Remove-Item -LiteralPath $RootExePath -Force
}

if (-not $SkipInstaller) {
    Invoke-InnoSetupBuild
}

Write-Host ""
Write-Host "Build finished."
Write-Host "App folder: $DistDir\\Jarvis"
Write-Host "App exe: $AppExePath"
Write-Host "Installer script: $InstallerScriptPath"
Write-Host "Installer output: $InstallerOutputPath"
