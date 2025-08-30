"""
Flask-WTF forms for the application
"""

from .auth_forms import LoginForm, RegistrationForm
from .contract_forms import ContractForm
from .client_forms import ClientForm

__all__ = ['LoginForm', 'RegistrationForm', 'ContractForm', 'ClientForm']
