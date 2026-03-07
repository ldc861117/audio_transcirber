from flask_cors import CORS

cors = CORS()

def init_extensions(app):
    cors.init_app(app, origins=app.config.get('CORS_ORIGINS', ['*']))
