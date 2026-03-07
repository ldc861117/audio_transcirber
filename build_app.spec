# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for Audio Transcriber standalone macOS app

from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all pywebview files (submodules, data, binaries)
webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=webview_binaries,
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
    ] + webview_datas,
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
        'audioop', 'pyaudioop',  # Python 3.13+ compat via audioop-lts
        'docx', 'reportlab',
        # Native window (pywebview + pyobjc)
        'objc', 'Foundation', 'AppKit', 'WebKit',
        'PyObjCTools', 'PyObjCTools.Conversion',
    ] + webview_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=False,       # No terminal window for the app
    disable_windowed_traceback=False,
    argv_emulation=True,
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
app = BUNDLE(
    coll,
    name='Audio Transcriber.app',
    icon=None,
    bundle_identifier='com.audiotranscriber.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleName': 'Audio Transcriber',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '12.0',
    },
)
