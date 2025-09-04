"""
Contract document models for multiple document support
"""
from datetime import datetime
import os

from app import db


class ContractDocument(db.Model):
    """Model for storing multiple documents per contract"""

    __tablename__ = "contract_documents"

    id = db.Column(db.Integer, primary_key=True)
    contract_id = db.Column(
        db.Integer, db.ForeignKey("contracts.id"), nullable=False, index=True
    )
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    document_type = db.Column(db.String(100), default="contract", nullable=False)  # contract, amendment, attachment, etc.
    description = db.Column(db.String(500), nullable=True)  # Optional description
    uploaded_by = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)  # Mark primary document

    # Relationships
    contract = db.relationship("Contract", back_populates="documents")
    uploader = db.relationship("User", lazy="joined")

    def __repr__(self):
        return f"<ContractDocument {self.file_name} for Contract {self.contract_id}>"

    def to_dict(self):
        """Convert document to dictionary for API responses"""
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "file_name": self.file_name,
            "original_filename": self.original_filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "document_type": self.document_type,
            "description": self.description,
            "uploaded_by": self.uploaded_by,
            "uploader_username": self.uploader.username if self.uploader else None,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "is_primary": self.is_primary,
        }

    def get_file_size_human(self):
        """Get human-readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} bytes"
        elif self.file_size < 1048576:
            return f"{(self.file_size / 1024):.1f} KB"
        else:
            return f"{(self.file_size / 1048576):.1f} MB"

    def get_file_icon(self):
        """Get Bootstrap icon class based on file type"""
        if self.mime_type:
            if 'pdf' in self.mime_type:
                return 'bi-file-earmark-pdf'
            elif 'word' in self.mime_type or 'msword' in self.mime_type:
                return 'bi-file-earmark-word'
            elif 'text' in self.mime_type:
                return 'bi-file-earmark-text'
            elif 'rtf' in self.mime_type:
                return 'bi-file-earmark-richtext'
        return 'bi-file-earmark'

    def delete_file_from_disk(self):
        """Delete the physical file from disk"""
        try:
            if self.file_path and os.path.exists(self.file_path):
                os.remove(self.file_path)
                return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error deleting file {self.file_path}: {e}")
        return False
