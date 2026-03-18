import os
import secrets
from datetime import datetime, timezone
from flask import g, current_app
from .models import User
from .jwt_manager import create_access_token, create_refresh_token
from backend.db.base import db

class DesktopAdapter:
    """
    Adapter for desktop mode to handle automatic authentication
    and local user management.
    """

    @staticmethod
    def get_default_user():
        """
        Returns the default local user for desktop mode.
        Creates one if it doesn't exist.
        """
        username = "desktop_user"
        user = User.get_by_username(username)

        if not user:
            # Create a default user for desktop mode
            # We use a random password since it won't be used for direct login
            email = "desktop@local.host"
            password = secrets.token_hex(16)
            user = User.create(username, email, password, role='admin')

            # Note: Track B's ensure_subscription should be called here if available
            try:
                from backend.subscriptions.quota_service import QuotaService
                if hasattr(QuotaService, '_ensure_subscription'):
                    QuotaService._ensure_subscription(user.id)
                elif hasattr(QuotaService, 'ensure_subscription'):
                    QuotaService.ensure_subscription(user.id)
            except (ImportError, AttributeError):
                pass

        return user

    @staticmethod
    def setup_desktop_auth(app):
        """
        Configures the app for desktop-friendly authentication.
        """
        if not os.environ.get('DESKTOP_MODE') == 'true':
            return

        @app.before_request
        def auto_authenticate():
            # In desktop mode, we can auto-login the default user if no token is provided
            from flask import request
            auth_header = request.headers.get('Authorization')

            if not auth_header or not auth_header.startswith('Bearer '):
                user = DesktopAdapter.get_default_user()
                g.current_user = user
                # We don't inject the token into the response here as it's a before_request
                # The frontend in desktop mode should ideally call an endpoint to get tokens
                # or we can provide a special bypass in decorators.
