# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 需要包含的文件
added_files = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('src', 'src'),
]

# 隐藏导入（PyInstaller可能检测不到的模块）
hiddenimports = [
    'flask',
    'flask.cli',
    'werkzeug.middleware.proxy_fix',
    'graphviz',
    'pandas',
    'pandas._libs.tslibs.base',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'pandas._libs.skiplist',
    'waitress',
    'waitress.server',
    'src.engine',
    'src.grammar',
    'src.parser',
    'src.utils',
    'src.visualizer',
]

# 排除不需要的模块（减小体积）
excludes = [
    'matplotlib',
    'numpy',
    'scipy',
    'tensorflow',
    'keras',
    'sklearn',
    'PIL',
    'IPython',
    'jupyter',
    'notebook',
    'qtpy',
    'PyQt5',
    'PySide2',
    'tkinter',
    'test',
    'unittest',
]

# 主配置
a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 创建单个exe文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LR0_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口（用于显示日志）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

)