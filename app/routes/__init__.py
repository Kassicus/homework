"""
Route blueprints for Contract Management Platform
"""
from .main import main_bp
from .auth import auth_bp
from .contracts import contracts_bp
from .clients import clients_bp
from .dashboard import dashboard_bp

__all__ = ["main_bp", "auth_bp", "contracts_bp", "clients_bp", "dashboard_bp"]
