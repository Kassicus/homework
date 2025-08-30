"""
Client model for storing client information
"""
from datetime import datetime

from app import db


class Client(db.Model):
    """Client model for storing client information"""

    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    organization = db.Column(db.String(200), nullable=True, index=True)
    email = db.Column(db.String(120), nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    contracts = db.relationship("Contract", lazy="dynamic", back_populates="client")

    def __repr__(self):
        return f"<Client {self.name}>"

    def to_dict(self):
        """Convert client to dictionary for API responses"""
        try:
            contract_count = self.contracts.count()
        except Exception:
            # Fallback to direct database query if relationship fails
            from app.models.contract import Contract
            contract_count = Contract.query.filter_by(client_id=self.id, deleted_at=None).count()
            
        return {
            "id": self.id,
            "name": self.name,
            "organization": self.organization,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "contract_count": contract_count,
        }

    @property
    def display_name(self):
        """Return display name (organization + name or just name)"""
        if self.organization:
            return f"{self.organization} - {self.name}"
        return self.name
    
    @property
    def contract_count(self):
        """Return the number of active contracts for this client"""
        try:
            return self.contracts.filter_by(deleted_at=None).count()
        except Exception:
            # Fallback to direct database query if relationship fails
            from app.models.contract import Contract
            return Contract.query.filter_by(client_id=self.id, deleted_at=None).count()

    def get_active_contracts(self):
        """Get all active contracts for this client"""
        return self.contracts.filter_by(status="active").all()

    def get_expiring_contracts(self, days=30):
        """Get contracts expiring within specified days"""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow().date() + timedelta(days=days)
        # Use the relationship to filter contracts
        return (
            self.contracts.filter_by(status="active")
            .filter(self.contracts.any(expiration_date <= cutoff_date))
            .all()
        )
