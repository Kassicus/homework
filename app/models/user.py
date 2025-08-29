"""
User model for authentication and authorization
"""
from datetime import datetime

from flask_login import UserMixin

from app import db, login_manager


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    contracts_created = db.relationship(
        "Contract",
        backref="creator",
        lazy="dynamic",
        foreign_keys="Contract.created_by",
    )
    status_changes = db.relationship(
        "ContractStatusHistory", backref="changed_by_user", lazy="dynamic"
    )
    access_history = db.relationship(
        "ContractAccessHistory", backref="accessed_by_user", lazy="dynamic"
    )

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        """Set password hash"""
        import bcrypt

        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode(
            "utf-8"
        )

    def check_password(self, password):
        """Check password against hash"""
        import bcrypt

        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def get_id(self):
        """Return user ID for Flask-Login"""
        return str(self.id)

    @property
    def is_authenticated(self):
        """Check if user is authenticated"""
        return True

    @property
    def is_anonymous(self):
        """Check if user is anonymous"""
        return False

    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    return User.query.get(int(user_id))
