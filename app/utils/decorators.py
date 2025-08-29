"""
Decorator utility functions for Contract Management Platform
"""
import logging
from functools import wraps

from flask import current_app, flash, redirect, request, url_for
from flask_login import current_user

logger = logging.getLogger(__name__)


def admin_required(f):
    """Decorator to require admin privileges"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))

        if not current_user.is_admin:
            flash("Access denied. Admin privileges required.", "error")
            return redirect(url_for("dashboard.index"))

        return f(*args, **kwargs)

    return decorated_function


def log_activity(activity_type):
    """Decorator to log user activity"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Log activity before function execution
                if current_user.is_authenticated:
                    logger.info(
                        f"User {current_user.username} performed {activity_type}"
                    )

                result = f(*args, **kwargs)

                # Log successful completion
                if current_user.is_authenticated:
                    logger.info(
                        f"User {current_user.username} completed {activity_type} successfully"
                    )

                return result

            except Exception as e:
                # Log error
                if current_user.is_authenticated:
                    logger.error(
                        f"User {current_user.username} failed {activity_type}: {e}"
                    )
                raise

        return decorated_function

    return decorator


def validate_file_upload(f):
    """Decorator to validate file uploads"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from app.utils.validators import validate_file_extension, validate_file_size

        # Check if file was uploaded
        if "contract_file" in request.files:
            file = request.files["contract_file"]

            if file and file.filename:
                # Validate file extension
                if not validate_file_extension(file.filename):
                    flash(
                        "Invalid file type. Please upload a PDF, DOCX, DOC, TXT, or RTF file.",
                        "error",
                    )
                    return redirect(request.url)

                # Validate file size
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Reset to beginning

                if not validate_file_size(file_size):
                    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 131072000)
                    flash(
                        f"File too large. Maximum size is {format_file_size(max_size)}.",
                        "error",
                    )
                    return redirect(request.url)

        return f(*args, **kwargs)

    return decorated_function


def handle_errors(f):
    """Decorator to handle common errors gracefully"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValueError as e:
            flash(str(e), "error")
            return redirect(request.url)
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}")
            flash("An unexpected error occurred. Please try again.", "error")
            return redirect(request.url)

    return decorated_function


def cache_result(timeout=300):
    """Simple decorator to cache function results (placeholder for future Redis implementation)"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implement Redis caching
            # For now, just call the function directly
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def rate_limit(requests_per_minute=60):
    """Rate limiting decorator (placeholder for future implementation)"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # TODO: Implement rate limiting
            # For now, just call the function directly
            return f(*args, **kwargs)

        return decorated_function

    return decorator
