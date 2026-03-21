import os
from flask import Flask, jsonify
from backend.db.base import db, init_db
from backend.extensions import init_extensions
from backend.config import configs

def create_app(config_name='development'):
    # Always load .env regardless of entry point (start.sh uses python -c, not __main__)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    app = Flask(__name__)
    app.config.from_object(configs[config_name])

    # Init database
    init_db(app)

    # Init extensions (CORS, etc.)
    init_extensions(app)

    # Register blueprints
    try:
        from backend.auth.routes import auth_bp
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

    from backend.recordings.routes import recordings_bp
    app.register_blueprint(recordings_bp, url_prefix='/api/v2/recordings')

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": {"code": "BAD_REQUEST", "message": str(e.description if hasattr(e, 'description') else e)}}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": {"code": "AUTH_REQUIRED", "message": "Authentication required"}}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({"error": {"code": "FORBIDDEN", "message": "Access denied"}}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": {"code": "NOT_FOUND", "message": "Resource not found"}}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}), 500

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
