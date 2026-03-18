import os
import logging
from flask import Flask, jsonify
from backend.db.base import db, init_db
from backend.extensions import init_extensions
from backend.config import configs
from backend.errors import register_error_handlers

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(configs[config_name])

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(logging.INFO)

    # Init database
    init_db(app)

    # Init extensions (CORS, etc.)
    init_extensions(app)

    # Register blueprints
    try:
        from backend.auth.routes import auth_bp
        from backend.auth.jwt_manager import validate_jwt_secrets
        with app.app_context():
            validate_jwt_secrets()
        app.register_blueprint(auth_bp, url_prefix='/api/v2/auth')
    except ImportError:
        app.logger.warning("Auth module not available, skipping...")

    try:
        from backend.subscriptions.routes import subscription_bp
        app.register_blueprint(subscription_bp, url_prefix='/api/v2/subscriptions')
    except ImportError:
        app.logger.warning("Subscription module not available, skipping...")

    from backend.transcriptions.routes import transcription_bp
    app.register_blueprint(transcription_bp, url_prefix='/api/v2/transcriptions')

    from backend.speakers.routes import speaker_bp
    app.register_blueprint(speaker_bp, url_prefix='/api/v2/speakers')

    from backend.exports.routes import export_bp
    app.register_blueprint(export_bp, url_prefix='/api/v2/export')

    # Global error handlers
    register_error_handlers(app)

    # Health check
    @app.route('/api/v2/health')
    def health():
        return {"status": "ok"}

    return app

# Standalone entry point
if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    app = create_app(os.environ.get('FLASK_ENV', 'development'))
    app.run(host='0.0.0.0', port=5099, debug=True)
