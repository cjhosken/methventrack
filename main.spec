# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('path_to_ffmpeg_binary', 'imageio_ffmpeg'),
        # Add other resources here
    ],
    hiddenimports=['pycolmap', 'pxr', 'imageio_ffmpeg'],
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
    upx=True,
    console=True,  # GUI app
    icon='icon.jpg',  # optional
)