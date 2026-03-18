from datetime import datetime, timezone
from ..db.base import db

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    tier = db.Column(db.String(20), default='free')              # free | basic | pro
    billing_cycle = db.Column(db.String(10), nullable=True)      # monthly | yearly | None(free)
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='active')          # active | cancelled | past_due
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    monthly_minutes_limit = db.Column(db.Integer, default=60)
    minutes_used = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class QuotaUsage(db.Model):
    __tablename__ = 'quota_usage'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.String(64), nullable=False)
    minutes_used = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Invoice(db.Model):
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_invoice_id = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.Integer, nullable=False)    # cents
    currency = db.Column(db.String(3), default='cny')
    status = db.Column(db.String(20))                 # paid | failed | refunded
    description = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
