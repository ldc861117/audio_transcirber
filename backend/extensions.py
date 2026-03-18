from flask_cors import CORS

cors = CORS()

def init_extensions(app):
    # Desktop app (pywebview) sends requests from file:// or localhost origins
    # Production Cloud Run needs to accept these cross-origin requests
    cors.init_app(app, origins="*", supports_credentials=True)
