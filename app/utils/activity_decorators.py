"""
Decorators for automatic activity logging
"""
from functools import wraps
from flask import request
from flask_login import current_user

from app.services.activity_service import log_user_activity
from app.models.activity_log import ActivityLog


def log_activity(action, resource_type, get_resource_info=None):
    """
    Decorator to automatically log user activities
    
    Args:
        action: Action being performed (view, create, update, delete)
        resource_type: Type of resource (contract, client, user)
        get_resource_info: Function to extract resource info from view args/kwargs
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Execute the original function
                result = func(*args, **kwargs)
                
                # Extract resource information
                resource_id = None
                resource_title = None
                
                if get_resource_info:
                    resource_info = get_resource_info(*args, **kwargs)
                    if isinstance(resource_info, tuple):
                        resource_id, resource_title = resource_info
                    else:
                        resource_id = resource_info
                elif 'id' in kwargs:
                    resource_id = kwargs['id']
                
                # Log the activity as successful
                log_user_activity(
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    resource_title=resource_title,
                    success=True
                )
                
                return result
                
            except Exception as e:
                # Log the activity as failed
                log_user_activity(
                    action=action,
                    resource_type=resource_type,
                    resource_id=kwargs.get('id'),
                    success=False,
                    error_message=str(e)
                )
                # Re-raise the exception
                raise
        
        return wrapper
    return decorator


def log_view(resource_type, get_resource_info=None):
    """Decorator for logging page views"""
    return log_activity(ActivityLog.ACTION_VIEW, resource_type, get_resource_info)


def log_create(resource_type, get_resource_info=None):
    """Decorator for logging resource creation"""
    return log_activity(ActivityLog.ACTION_CREATE, resource_type, get_resource_info)


def log_update(resource_type, get_resource_info=None):
    """Decorator for logging resource updates"""
    return log_activity(ActivityLog.ACTION_UPDATE, resource_type, get_resource_info)


def log_delete(resource_type, get_resource_info=None):
    """Decorator for logging resource deletion"""
    return log_activity(ActivityLog.ACTION_DELETE, resource_type, get_resource_info)


def log_restore(resource_type, get_resource_info=None):
    """Decorator for logging resource restoration"""
    return log_activity(ActivityLog.ACTION_RESTORE, resource_type, get_resource_info)


# Helper functions for extracting resource information
def get_contract_info(contract_id=None, *args, **kwargs):
    """Extract contract information for logging"""
    from app.models.contract import Contract
    
    if contract_id is None:
        contract_id = kwargs.get('id')
    
    if contract_id:
        contract = Contract.query.get(contract_id)
        if contract:
            return contract_id, contract.title
    
    return contract_id, None


def get_client_info(client_id=None, *args, **kwargs):
    """Extract client information for logging"""
    from app.models.client import Client
    
    if client_id is None:
        client_id = kwargs.get('id')
    
    if client_id:
        client = Client.query.get(client_id)
        if client:
            return client_id, client.name
    
    return client_id, None


def get_user_info(user_id=None, *args, **kwargs):
    """Extract user information for logging"""
    from app.models.user import User
    
    if user_id is None:
        user_id = kwargs.get('id')
    
    if user_id:
        user = User.query.get(user_id)
        if user:
            return user_id, user.username
    
    return user_id, None


# Admin-only decorator
def admin_required(func):
    """Decorator to require admin access"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            from flask import redirect, url_for, flash
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin:
            from flask import abort
            # Log unauthorized access attempt
            log_user_activity(
                action='access_denied',
                resource_type='admin',
                success=False,
                error_message='User attempted to access admin-only resource'
            )
            abort(403)
        
        return func(*args, **kwargs)
    
    return wrapper
