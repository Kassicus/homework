"""
Activity logging models for tracking user actions
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, func, desc
from sqlalchemy.orm import relationship

from app.logging_db import LoggingBase, get_logging_session


class ActivityLog(LoggingBase):
    """Activity log model for tracking user actions"""

    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True, index=True)
    resource_title = Column(String(300), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Action constants
    ACTION_VIEW = "view"
    ACTION_CREATE = "create"
    ACTION_UPDATE = "update"
    ACTION_DELETE = "delete"
    ACTION_RESTORE = "restore"
    
    # DocuSign-specific actions
    ACTION_DOCUSIGN_SEND = "docusign_send"
    ACTION_DOCUSIGN_CHECK = "docusign_check"
    ACTION_DOCUSIGN_VOID = "docusign_void"
    ACTION_DOCUSIGN_STATUS_CHANGE = "docusign_status_change"
    
    # Document-specific actions
    ACTION_DOCUMENT_UPLOAD = "document_upload"
    ACTION_DOCUMENT_DELETE = "document_delete"
    ACTION_DOCUMENT_DOWNLOAD = "document_download"
    ACTION_DOCUMENT_SET_PRIMARY = "document_set_primary"
    ACTION_DOCUMENT_MIGRATE = "document_migrate"

    # Resource type constants
    RESOURCE_CONTRACT = "contract"
    RESOURCE_CLIENT = "client"
    RESOURCE_USER = "user"
    RESOURCE_DOCUSIGN = "docusign"
    RESOURCE_DOCUMENT = "document"

    def __repr__(self):
        return f"<ActivityLog {self.user_id}:{self.action}:{self.resource_type}>"

    def to_dict(self):
        """Convert activity log to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_title": self.resource_title,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def get_user_recent_activity(cls, user_id, limit=10):
        """Get recent activity for a specific user"""
        session = get_logging_session()
        try:
            return (
                session.query(cls)
                .filter_by(user_id=user_id)
                .order_by(cls.timestamp.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()

    @classmethod
    def get_most_viewed_resources(cls, resource_type, limit=10, days=30):
        """Get most viewed resources of a specific type"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        session = get_logging_session()
        
        try:
            return (
                session.query(
                    cls.resource_id,
                    cls.resource_title,
                    func.count(cls.id).label("view_count")
                )
                .filter(
                    cls.action == cls.ACTION_VIEW,
                    cls.resource_type == resource_type,
                    cls.timestamp >= cutoff_date,
                    cls.resource_id.isnot(None)
                )
                .group_by(cls.resource_id, cls.resource_title)
                .order_by(desc("view_count"))
                .limit(limit)
                .all()
            )
        finally:
            session.close()


class ContractVersion(LoggingBase):
    """Contract version history for tracking field-level changes"""

    __tablename__ = "contract_versions"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    field_name = Column(String(100), nullable=False, index=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    def __repr__(self):
        return f"<ContractVersion {self.contract_id}:{self.field_name}>"

    def to_dict(self):
        """Convert contract version to dictionary"""
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "user_id": self.user_id,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def get_contract_history(cls, contract_id, limit=50):
        """Get version history for a specific contract"""
        session = get_logging_session()
        try:
            return (
                session.query(cls)
                .filter_by(contract_id=contract_id)
                .order_by(cls.timestamp.desc())
                .limit(limit)
                .all()
            )
        finally:
            session.close()
