from flask_cors import CORS

cors = CORS()

def init_extensions(app):
    # Tighten CORS to use origins from app.config['CORS_ORIGINS']
    # Defaults to '*' if not configured (for desktop app compatibility)
    origins = app.config.get('CORS_ORIGINS', '*')
    cors.init_app(app, origins=origins, supports_credentials=True)
