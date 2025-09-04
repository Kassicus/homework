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


# DocuSign-specific logging decorators
def log_docusign_send(get_resource_info=None):
    """Decorator for logging DocuSign document sending"""
    return log_activity(ActivityLog.ACTION_DOCUSIGN_SEND, ActivityLog.RESOURCE_CONTRACT, get_resource_info)


def log_docusign_check(get_resource_info=None):
    """Decorator for logging DocuSign status checks"""
    return log_activity(ActivityLog.ACTION_DOCUSIGN_CHECK, ActivityLog.RESOURCE_CONTRACT, get_resource_info)


def log_docusign_void(get_resource_info=None):
    """Decorator for logging DocuSign envelope voiding"""
    return log_activity(ActivityLog.ACTION_DOCUSIGN_VOID, ActivityLog.RESOURCE_CONTRACT, get_resource_info)


# Document-specific logging decorators
def log_document_upload(get_resource_info=None):
    """Decorator for logging document uploads"""
    return log_activity(ActivityLog.ACTION_DOCUMENT_UPLOAD, ActivityLog.RESOURCE_DOCUMENT, get_resource_info)


def log_document_delete(get_resource_info=None):
    """Decorator for logging document deletions"""
    return log_activity(ActivityLog.ACTION_DOCUMENT_DELETE, ActivityLog.RESOURCE_DOCUMENT, get_resource_info)


def log_document_download(get_resource_info=None):
    """Decorator for logging document downloads"""
    return log_activity(ActivityLog.ACTION_DOCUMENT_DOWNLOAD, ActivityLog.RESOURCE_DOCUMENT, get_resource_info)


def log_document_set_primary(get_resource_info=None):
    """Decorator for logging setting document as primary"""
    return log_activity(ActivityLog.ACTION_DOCUMENT_SET_PRIMARY, ActivityLog.RESOURCE_DOCUMENT, get_resource_info)


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


def get_docusign_info(contract_id=None, *args, **kwargs):
    """Extract DocuSign-related information for logging"""
    from app.models.contract import Contract
    
    if contract_id is None:
        contract_id = kwargs.get('contract_id') or kwargs.get('id')
    
    if contract_id:
        contract = Contract.query.get(contract_id)
        if contract:
            # Include DocuSign envelope ID in the title for better tracking
            title = f"{contract.title}"
            if contract.docusign_envelope_id:
                title += f" (Envelope: {contract.docusign_envelope_id[:8]}...)"
            return contract_id, title
    
    return contract_id, None


def get_document_info(document_id=None, contract_id=None, *args, **kwargs):
    """Extract document information for logging"""
    from app.models.contract_document import ContractDocument
    from app.models.contract import Contract
    
    # Try to get document_id from various sources
    if document_id is None:
        document_id = kwargs.get('document_id') or kwargs.get('id')
    
    if contract_id is None:
        contract_id = kwargs.get('contract_id')
    
    if document_id:
        document = ContractDocument.query.get(document_id)
        if document:
            # Create descriptive title with contract context
            contract = Contract.query.get(document.contract_id) if document.contract_id else None
            contract_title = contract.title if contract else f"Contract {document.contract_id}"
            
            title = f"{document.original_filename}"
            title += f" ({document.get_file_size_human()})"
            title += f" - {contract_title}"
            if document.is_primary:
                title += " [PRIMARY]"
            
            return document_id, title
    
    return document_id, None


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
