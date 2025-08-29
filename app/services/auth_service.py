"""
Authentication service for user management
"""
from datetime import datetime, timedelta
import logging

import bcrypt
from flask import current_app, request
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.models.user import User


logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication and user management"""

    @staticmethod
    def hash_password(password):
        """Hash password using bcrypt"""
        try:
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
            return password_hash.decode("utf-8")
        except Exception as e:
            logger.error(f"Error hashing password: {e}")
            raise

    @staticmethod
    def verify_password(password, password_hash):
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            )
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    @staticmethod
    def register_user(username, email, password, organization=None):
        """Register a new user"""
        try:
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                raise ValueError("Username already exists")

            if User.query.filter_by(email=email).first():
                raise ValueError("Email already exists")

            # Create new user
            user = User(username=username, email=email, is_active=True, is_admin=False)
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            logger.info(f"New user registered: {username} ({email})")
            return user

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user {username}: {e}")
            raise

    @staticmethod
    def authenticate_user(username, password):
        """Authenticate user with username and password"""
        try:
            user = User.query.filter_by(username=username).first()

            if user and user.check_password(password):
                if not user.is_active:
                    raise ValueError("User account is inactive")

                logger.info(f"User authenticated successfully: {username}")
                return user
            else:
                logger.warning(
                    f"Failed authentication attempt for username: {username}"
                )
                return None

        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            raise

    @staticmethod
    def login_user_service(user, remember=False):
        """Login user and create session"""
        try:
            login_user(user, remember=remember)

            # Log successful login
            logger.info(
                f"User logged in: {user.username} from IP: {request.remote_addr}"
            )

            return True

        except Exception as e:
            logger.error(f"Error during login: {e}")
            raise

    @staticmethod
    def logout_user_service():
        """Logout current user"""
        try:
            if current_user.is_authenticated:
                username = current_user.username
                logout_user()
                logger.info(f"User logged out: {username}")

            return True

        except Exception as e:
            logger.error(f"Error during logout: {e}")
            raise

    @staticmethod
    def change_password(user_id, current_password, new_password):
        """Change user password"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")

            if not user.check_password(current_password):
                raise ValueError("Current password is incorrect")

            user.set_password(new_password)
            db.session.commit()

            logger.info(f"Password changed for user: {user.username}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing password for user {user_id}: {e}")
            raise

    @staticmethod
    def reset_password(email):
        """Reset user password (placeholder for future email functionality)"""
        try:
            user = User.query.filter_by(email=email).first()
            if not user:
                raise ValueError("User not found")

            # Generate temporary password
            import secrets
            import string

            temp_password = "".join(
                secrets.choice(string.ascii_letters + string.digits) for _ in range(12)
            )

            user.set_password(temp_password)
            db.session.commit()

            logger.info(f"Password reset for user: {user.username}")
            # TODO: Send email with temporary password

            return temp_password

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error resetting password for email {email}: {e}")
            raise

    @staticmethod
    def update_user_status(user_id, is_active, updated_by):
        """Update user active status (admin only)"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("User not found")

            old_status = user.is_active
            user.is_active = is_active
            db.session.commit()

            logger.info(
                f"User status updated by {updated_by.username}: {user.username} - {old_status} -> {is_active}"
            )
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user status for user {user_id}: {e}")
            raise

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)

    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()

    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_all_users():
        """Get all users (admin only)"""
        return User.query.all()

    @staticmethod
    def get_active_users():
        """Get all active users"""
        return User.query.filter_by(is_active=True).all()
