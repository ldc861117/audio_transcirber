from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db.base import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')        # user | admin
    status = db.Column(db.String(20), default='active')    # active | suspended | deleted
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_login_at = db.Column(db.DateTime, nullable=True)

    # subscription relationship will be defined by Track B. 
    # For now, we only declare it if Track B has not yet created the model.
    # To avoid "Relationship user.subscription will copy column subscriptions.user_id to users.id, which conflicts with relationship(s)"
    # We follow the contract.
    subscription = db.relationship('Subscription', backref='user', uselist=False, lazy='joined')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def create(username, email, password, role='user'):
        user = User(
            username=username,
            email=email,
            role=role,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate(identifier, password):
        """Authenticate by username or email."""
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()
        if user and user.check_password(password):
            return user
        return None

    @staticmethod
    def get_by_id(user_id):
        return db.session.get(User, user_id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_by_username(username):
        return User.query.filter_by(username=username).first()


class RefreshToken(db.Model):
    __tablename__ = 'refresh_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(user_id, token_hash, expires_at):
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.session.add(rt)
        db.session.commit()
        return rt

    @staticmethod
    def find_valid(token_hash):
        return RefreshToken.query.filter_by(
            token_hash=token_hash,
            revoked=False
        ).filter(RefreshToken.expires_at > datetime.now(timezone.utc)).first()

    def revoke(self):
        self.revoked = True
        db.session.commit()

    @staticmethod
    def revoke_all_for_user(user_id):
        RefreshToken.query.filter_by(user_id=user_id, revoked=False).update({'revoked': True})
        db.session.commit()

# Mock Subscription class if it doesn't exist to allow relationship to work
# This is a bit tricky if multiple tracks are working.
# But for py_compile to work, it might be needed if SQLAlchemy validates it immediately.
# Actually, SQLAlchemy usually doesn't validate until first use.
