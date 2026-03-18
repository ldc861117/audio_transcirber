from flask import jsonify

def make_error_response(code, message, status_code=400):
    return jsonify({
        "error": {
            "code": code,
            "message": message
        }
    }), status_code

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return make_error_response("BAD_REQUEST", str(e.description if hasattr(e, 'description') else e), 400)

    @app.errorhandler(401)
    def unauthorized(e):
        return make_error_response("AUTH_REQUIRED", "Authentication required", 401)

    @app.errorhandler(403)
    def forbidden(e):
        return make_error_response("FORBIDDEN", "Access denied", 403)

    @app.errorhandler(404)
    def not_found(e):
        return make_error_response("NOT_FOUND", "Resource not found", 404)

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return make_error_response("RATE_LIMIT_EXCEEDED", "Too many requests", 429)

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal Server Error: {e}")
        return make_error_response("INTERNAL_ERROR", "Internal server error", 500)
