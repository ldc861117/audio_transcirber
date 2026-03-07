from .routes import subscription_bp

def init_subscriptions(app):
    app.register_blueprint(subscription_bp, url_prefix='/api/v2/subscriptions')
