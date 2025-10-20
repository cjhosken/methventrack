# -*- mode: python ; coding: utf-8 -*-

import glob
import os
import site
from imageio_ffmpeg import get_ffmpeg_exe

block_cipher = None

# ----------------------------
# 1️⃣ PXr hidden imports & binaries
# ----------------------------
hiddenimports = [
    'pxr.Tf._tf',
    'pxr.Sdf._sdf',
    'pxr.Usd._usd',
    'pxr.UsdGeom._usdGeom',
    'pxr.Gf._gf',
    'pxr.Vt._vt',
    'pxr.UsdUtils._usdUtils',
    'pxr.UsdShade._usdShade',
]

# Locate pxr site-packages path
pxr_path = os.path.join(site.getsitepackages()[0], "pxr")
datas = []

# Include all .pyd files
for f in glob.glob(os.path.join(pxr_path, "*.pyd")):
    datas.append((f, "pxr"))

# Include any dlls if on Windows
for f in glob.glob(os.path.join(pxr_path, "*.dll")):
    datas.append((f, "pxr"))

# ----------------------------
# 2️⃣ Include ffmpeg binary from imageio-ffmpeg
# ----------------------------
ffmpeg_bin = get_ffmpeg_exe()
datas.append((ffmpeg_bin, "imageio_ffmpeg"))

# ----------------------------
# 3️⃣ Analysis
# ----------------------------
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports + ['pycolmap', 'imageio_ffmpeg', 'PySide6'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

# ----------------------------
# 4️⃣ PYZ
# ----------------------------
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# ----------------------------
# 5️⃣ EXE
# ----------------------------
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='MethvenTrack',
    debug=False,
    strip=False,
    upx=True,
    console=False,  # GUI app
    icon='icon.ico',  # replace with your icon if you have one
)
