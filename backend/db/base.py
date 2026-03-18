from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    with app.app_context():
        # Import all models so SQLAlchemy registers them before create_all
        try:
            from backend.auth.models import User, RefreshToken  # noqa: F401
        except ImportError:
            pass
        try:
            from backend.subscriptions.models import Subscription, QuotaUsage, Invoice  # noqa: F401
        except ImportError:
            pass
        try:
            db.create_all()
        except Exception:
            pass  # Table already exists (race condition with multiple workers)

