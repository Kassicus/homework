"""
Validation utility functions for Contract Management Platform
"""
import os

from flask import current_app
from werkzeug.utils import secure_filename


def validate_file_extension(filename):
    """Validate file extension against allowed types"""
    if not filename:
        return False

    allowed_extensions = current_app.config.get("ALLOWED_EXTENSIONS", [])
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def validate_file_size(file_size):
    """Validate file size against maximum allowed size"""
    max_size = current_app.config.get("MAX_CONTENT_LENGTH", 131072000)  # 125MB default
    return file_size <= max_size


def validate_contract_data(data):
    """Validate contract form data"""
    errors = []

    if not data.get("title"):
        errors.append("Title is required")

    if not data.get("client_id"):
        errors.append("Client is required")

    if not data.get("contract_type"):
        errors.append("Contract type is required")

    return errors


def validate_client_data(data):
    """Validate client form data"""
    errors = []

    if not data.get("name"):
        errors.append("Client name is required")

    return errors


def validate_user_data(data):
    """Validate user form data"""
    errors = []

    if not data.get("username"):
        errors.append("Username is required")

    if not data.get("email"):
        errors.append("Email is required")

    if not data.get("password"):
        errors.append("Password is required")
    elif len(data.get("password", "")) < 6:
        errors.append("Password must be at least 6 characters long")

    return errors
