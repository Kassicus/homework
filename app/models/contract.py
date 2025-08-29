"""
Contract models for contract management
"""
from datetime import date, datetime

from sqlalchemy import event

from app import db


class Contract(db.Model):
    """Contract model for storing contract information"""

    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    client_id = db.Column(
        db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True
    )
    contract_type = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(50), default="draft", nullable=False, index=True)
    contract_value = db.Column(db.Numeric(15, 2), nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    file_name = db.Column(db.String(300), nullable=True)
    file_size = db.Column(db.Integer, nullable=True)
    mime_type = db.Column(db.String(100), nullable=True)
    extracted_text = db.Column(db.Text, nullable=True)
    created_date = db.Column(db.Date, nullable=False, default=date.today)
    effective_date = db.Column(db.Date, nullable=True)
    expiration_date = db.Column(db.Date, nullable=True)
    renewal_date = db.Column(db.Date, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True, index=True)
    created_by = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    status_history = db.relationship(
        "ContractStatusHistory",
        backref="contract",
        lazy="dynamic",
        order_by="ContractStatusHistory.changed_at.desc()",
    )
    access_history = db.relationship(
        "ContractAccessHistory",
        backref="contract",
        lazy="dynamic",
        order_by="ContractAccessHistory.accessed_at.desc()",
    )

    # Status constants
    STATUS_DRAFT = "draft"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_ACTIVE = "active"
    STATUS_EXPIRED = "expired"
    STATUS_TERMINATED = "terminated"
    STATUS_RENEWED = "renewed"
    STATUS_DELETED = "deleted"

    VALID_STATUSES = [
        STATUS_DRAFT,
        STATUS_UNDER_REVIEW,
        STATUS_ACTIVE,
        STATUS_EXPIRED,
        STATUS_TERMINATED,
        STATUS_RENEWED,
        STATUS_DELETED,
    ]

    def __repr__(self):
        return f"<Contract {self.title}>"

    def to_dict(self):
        """Convert contract to dictionary for API responses"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "client_id": self.client_id,
            "client_name": self.client.name if self.client else None,
            "contract_type": self.contract_type,
            "status": self.status,
            "contract_value": float(self.contract_value)
            if self.contract_value
            else None,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "created_date": self.created_date.isoformat()
            if self.created_date
            else None,
            "effective_date": self.effective_date.isoformat()
            if self.effective_date
            else None,
            "expiration_date": self.expiration_date.isoformat()
            if self.expiration_date
            else None,
            "renewal_date": self.renewal_date.isoformat()
            if self.renewal_date
            else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_by": self.created_by,
            "creator_username": self.creator.username if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_deleted": self.deleted_at is not None,
        }

    def update_status(self, new_status, changed_by, reason=None):
        """Update contract status and record in history"""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {new_status}")

        old_status = self.status
        self.status = new_status

        # Record status change
        status_history = ContractStatusHistory(
            contract_id=self.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            change_reason=reason,
        )

        db.session.add(status_history)
        return status_history

    def soft_delete(self, deleted_by):
        """Soft delete contract (mark as deleted but retain for 30 days)"""
        self.deleted_at = datetime.utcnow()
        self.update_status(self.STATUS_DELETED, deleted_by, "Contract soft deleted")

    def restore(self, restored_by):
        """Restore soft-deleted contract"""
        self.deleted_at = None
        self.update_status(
            self.STATUS_DRAFT, restored_by, "Contract restored from deletion"
        )

    def is_expired(self):
        """Check if contract is expired"""
        if not self.expiration_date:
            return False
        return self.expiration_date < date.today()

    def is_active(self):
        """Check if contract is currently active"""
        return self.status == self.STATUS_ACTIVE and not self.is_expired()

    def days_until_expiration(self):
        """Calculate days until expiration"""
        if not self.expiration_date:
            return None
        delta = self.expiration_date - date.today()
        return delta.days

    def log_access(self, user_id, access_type, ip_address=None, user_agent=None):
        """Log contract access"""
        access_log = ContractAccessHistory(
            contract_id=self.id,
            accessed_by=user_id,
            access_type=access_type,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.session.add(access_log)
        return access_log


class ContractStatusHistory(db.Model):
    """Contract status change history for audit trail"""

    __tablename__ = "contract_status_history"

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(
        db.Integer, db.ForeignKey("contracts.id"), nullable=False, index=True
    )
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_by = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    change_reason = db.Column(db.Text, nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ContractStatusHistory {self.contract_id}: {self.old_status} -> {self.new_status}>"

    def to_dict(self):
        """Convert status history to dictionary"""
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "changed_by": self.changed_by,
            "changed_by_username": (
                self.changed_by_user.username if self.changed_by_user else None
            ),
            "change_reason": self.change_reason,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }


class ContractAccessHistory(db.Model):
    """Contract access history for audit trail"""

    __tablename__ = "contract_access_history"

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(
        db.Integer, db.ForeignKey("contracts.id"), nullable=False, index=True
    )
    accessed_by = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    access_type = db.Column(db.String(50), nullable=False)  # 'view', 'download', 'edit'
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ContractAccessHistory {self.contract_id}: {self.access_type} by {self.accessed_by}>"

    def to_dict(self):
        """Convert access history to dictionary"""
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "accessed_by": self.accessed_by,
            "accessed_by_username": (
                self.accessed_by_user.username if self.accessed_by_user else None
            ),
            "access_type": self.access_type,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
        }


# Event listeners for automatic status updates
@event.listens_for(Contract, "before_update")
def before_contract_update(mapper, connection, target):
    """Automatically update status based on dates"""
    if target.expiration_date and target.expiration_date < date.today():
        if target.status == Contract.STATUS_ACTIVE:
            target.status = Contract.STATUS_EXPIRED
