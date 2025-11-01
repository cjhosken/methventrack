# -*- mode: python ; coding: utf-8 -*-
import os
import site
import pxr
from imageio_ffmpeg import get_ffmpeg_exe

block_cipher = None

# 1️⃣ Include ffmpeg binary
ffmpeg_bin = get_ffmpeg_exe()
datas = [(ffmpeg_bin, "imageio_ffmpeg")]

# 2️⃣ Include entire USD 'pxr' package intact
pxr_path = os.path.dirname(pxr.__file__)
datas.append((pxr_path, "pxr"))

datas.append(('icon.ico', '.'))  # 👈 Include icon file in root of dist folder

# 3️⃣ Build
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pycolmap', 'imageio_ffmpeg', 'PySide6',
        'pxr.Usd', 'pxr.Sdf', 'pxr.Tf', 'pxr.Gf', 'pxr.Vt', 'pxr.Ar'
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='MethvenTrack',
    debug=False,
    strip=False,
    upx=False,  # ⛔ Disable UPX; it can break USD .pyds
    console=True,
    icon='icon.ico',
)
