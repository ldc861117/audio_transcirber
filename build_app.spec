# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Flask-only binary (Electron handles the GUI)

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('configs', 'configs'),
        ('contracts.yaml', '.'),
        ('db', 'db'),
        ('models', 'models'),
        ('plans', 'plans'),
        ('routes', 'routes'),
        ('services', 'services'),
        ('templates', 'templates'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        # Flask & Extensions
        'flask', 'flask_cors', 'flask_login',
        # App modules
        'app_paths', 'auth', 'speaker', 'speaker_db', 'speaker_v2',
        # Routes
        'routes', 'routes.task_routes', 'routes.plan_routes',
        'routes.export_routes', 'routes.recording_routes',
        'routes.speaker_routes',
        # Services
        'services', 'services.task_service', 'services.speaker_service',
        'services.diarization_service', 'services.export_service',
        'services.plan_service', 'services.provider_service', 'services.quota_service',
        # DB & Models
        'db', 'db.task_db', 'models', 'models.task',
        # Plans
        'plans', 'plans.plan_db', 'plans.plan_config',
        # Configs
        'configs',
        # Third party
        'zhipuai', 'openai', 'pydub', 'dotenv', 'yaml',
        'numpy', 'scipy', 'onnxruntime',
        'docx', 'reportlab',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['webview'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Audio Transcriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,        # headless Flask server, stdout/stderr go to Electron
    disable_windowed_traceback=False,
    argv_emulation=False, # not a GUI app
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Audio Transcriber',
)
# No BUNDLE — Electron handles the .app wrapper
