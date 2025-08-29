"""
Route blueprints for Contract Management Platform
"""
from .auth import auth_bp
from .clients import clients_bp
from .contracts import contracts_bp
from .dashboard import dashboard_bp
from .main import main_bp

__all__ = ["main_bp", "auth_bp", "contracts_bp", "clients_bp", "dashboard_bp"]
