import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_dir = Path(SPECPATH)
logo_icon = project_dir / "build_assets" / "jarvis.ico"
version_info = project_dir / "build_assets" / "jarvis_version_info.txt"

datas = []
binaries = []
hiddenimports = []

for package_name in (
    "comtypes",
    "edge_tts",
    "pygame",
    "pycaw",
    "pyaudio",
    "pyttsx3",
    "speech_recognition",
    "pystray",
    "PIL",
    "tkinter",
):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package_name)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

python_tcl_root = Path(sys.base_prefix) / "tcl"
explicit_tcl_dirs = []

if python_tcl_root.exists():
    tcl_dirs = sorted(
        path for path in python_tcl_root.iterdir()
        if path.is_dir() and path.name.lower().startswith("tcl")
    )
    tk_dirs = sorted(
        path for path in python_tcl_root.iterdir()
        if path.is_dir() and path.name.lower().startswith("tk")
    )

    if tcl_dirs:
        explicit_tcl_dirs.append((tcl_dirs[-1], "_tcl_data"))
    if tk_dirs:
        explicit_tcl_dirs.append((tk_dirs[-1], "_tk_data"))

for source_dir, dest_dir in explicit_tcl_dirs:
    if source_dir.exists():
        for item in source_dir.rglob("*"):
            if item.is_file():
                relative_parent = item.relative_to(source_dir).parent
                target_dir = Path(dest_dir) / relative_parent
                datas.append((str(item), str(target_dir)))

hiddenimports += [
    "tkinter",
    "_tkinter",
    "tkinter.ttk",
    "tkinter.constants",
    "tkinter.filedialog",
    "tkinter.messagebox",
    "tkinter.font",
    "tkinter.scrolledtext",
    "PIL._tkinter_finder",
    "pystray._win32",
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="Jarvis",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(logo_icon) if logo_icon.exists() else None,
    version=str(version_info) if version_info.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Jarvis",
)
