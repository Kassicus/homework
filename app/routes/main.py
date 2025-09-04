"""
Main routes for Contract Management Platform
"""
from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home page - redirect to dashboard if logged in, otherwise redirect to login"""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    return redirect(url_for("auth.login"))





@main_bp.route("/help")
def help():
    """Help and documentation page"""
    return render_template("main/help.html")


@main_bp.route("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "contract-manager"}
