from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    # Skip create_all if it's sqlite and directory doesn't exist yet, 
    # or just let it fail gracefully if we can't create it.
    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        app.logger.warning(f"Could not create database tables: {e}")
