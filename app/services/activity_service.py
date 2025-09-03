"""
Activity logging service for tracking user actions
"""
import threading
from datetime import datetime
from queue import Queue
from typing import Optional

from flask import current_app, request
from flask_login import current_user

from app.logging_db import get_logging_session
from app.models.activity_log import ActivityLog, ContractVersion


class ActivityLogger:
    """Asynchronous activity logger"""
    
    def __init__(self):
        self.log_queue = Queue()
        self.worker_thread = None
        self.running = False
    
    def start(self):
        """Start the logging worker thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker, daemon=True)
            self.worker_thread.start()
            print("✓ Activity logging service started")
    
    def stop(self):
        """Stop the logging worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _worker(self):
        """Worker thread to process logging queue"""
        import time
        while self.running:
            try:
                # Use get with timeout to avoid blocking indefinitely
                try:
                    log_data = self.log_queue.get(timeout=1)
                    self._write_log(log_data)
                    self.log_queue.task_done()
                except:
                    # Timeout or empty queue, continue
                    time.sleep(0.1)
                    continue
            except Exception as e:
                # Log to console since current_app might not be available in thread
                print(f"Activity logging error: {e}")
    
    def _write_log(self, log_data):
        """Write log entry to database"""
        session = get_logging_session()
        if not session:
            print("No logging session available")
            return
            
        try:
            if log_data['type'] == 'activity':
                log_entry = ActivityLog(**log_data['data'])
                session.add(log_entry)
            elif log_data['type'] == 'version':
                version_entry = ContractVersion(**log_data['data'])
                session.add(version_entry)
            
            session.commit()
        except Exception as e:
            print(f"Failed to write log: {e}")
            session.rollback()
        finally:
            session.close()
    
    def log_activity(
        self,
        user_id: int,
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        resource_title: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Queue an activity log entry"""
        log_data = {
            'type': 'activity',
            'data': {
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'resource_title': resource_title,
                'success': success,
                'error_message': error_message,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'timestamp': datetime.utcnow()
            }
        }
        self.log_queue.put(log_data)
    
    def log_contract_change(
        self,
        contract_id: int,
        user_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str]
    ):
        """Queue a contract version entry"""
        version_data = {
            'type': 'version',
            'data': {
                'contract_id': contract_id,
                'user_id': user_id,
                'field_name': field_name,
                'old_value': str(old_value) if old_value is not None else None,
                'new_value': str(new_value) if new_value is not None else None,
                'timestamp': datetime.utcnow()
            }
        }
        self.log_queue.put(version_data)


# Global activity logger instance
activity_logger = ActivityLogger()


def log_user_activity(
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    resource_title: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    user_id: Optional[int] = None
):
    """
    Log user activity
    
    Args:
        action: Action performed (view, create, update, delete, restore)
        resource_type: Type of resource (contract, client, user)
        resource_id: ID of the resource
        resource_title: Title/name of the resource
        success: Whether the action was successful
        error_message: Error message if action failed
        user_id: User ID (defaults to current user)
    """
    try:
        # Get user ID
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                return  # Don't log anonymous actions
        
        # Get request info
        ip_address = None
        user_agent = None
        if request:
            ip_address = request.remote_addr
            user_agent = request.headers.get('User-Agent')
        
        # Queue the log entry
        activity_logger.log_activity(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_title=resource_title,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        print(f"Failed to log activity: {e}")


def log_contract_changes(contract, old_values, user_id=None):
    """
    Log field-level changes to a contract
    
    Args:
        contract: Contract object with new values
        old_values: Dictionary of old field values
        user_id: User ID making the changes
    """
    try:
        if user_id is None:
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                return
        
        # Track specific fields that we want to version
        tracked_fields = [
            'title', 'description', 'client_id', 'contract_type', 
            'status', 'contract_value', 'effective_date', 'expiration_date',
            'renewal_date'
        ]
        
        for field in tracked_fields:
            old_value = old_values.get(field)
            new_value = getattr(contract, field, None)
            
            # Convert dates to strings for comparison
            if hasattr(old_value, 'isoformat'):
                old_value = old_value.isoformat()
            if hasattr(new_value, 'isoformat'):
                new_value = new_value.isoformat()
            
            # Only log if value actually changed
            if str(old_value) != str(new_value):
                activity_logger.log_contract_change(
                    contract_id=contract.id,
                    user_id=user_id,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value
                )
    except Exception as e:
        print(f"Failed to log contract changes: {e}")


def get_user_activity_summary(user_id: int, limit: int = 10):
    """Get formatted activity summary for a user"""
    try:
        activities = ActivityLog.get_user_recent_activity(user_id, limit)
        
        formatted_activities = []
        for activity in activities:
            # Format the activity message
            action_text = {
                ActivityLog.ACTION_VIEW: "Viewed",
                ActivityLog.ACTION_CREATE: "Created",
                ActivityLog.ACTION_UPDATE: "Updated",
                ActivityLog.ACTION_DELETE: "Deleted",
                ActivityLog.ACTION_RESTORE: "Restored"
            }.get(activity.action, activity.action.title())
            
            resource_text = {
                ActivityLog.RESOURCE_CONTRACT: "contract",
                ActivityLog.RESOURCE_CLIENT: "client",
                ActivityLog.RESOURCE_USER: "user"
            }.get(activity.resource_type, activity.resource_type)
            
            if activity.resource_title:
                message = f"{action_text} {resource_text} '{activity.resource_title}'"
            else:
                message = f"{action_text} {resource_text}"
            
            formatted_activities.append({
                'message': message,
                'timestamp': activity.timestamp,
                'success': activity.success,
                'action': activity.action,
                'resource_type': activity.resource_type
            })
        
        return formatted_activities
    except Exception as e:
        print(f"Failed to get user activity for user {user_id}: {e}")
        return []
