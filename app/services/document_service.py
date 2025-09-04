"""
Document service for managing contract documents
"""
from datetime import datetime
import logging
import os

from app import db
from app.models.contract_document import ContractDocument
from app.services.file_service import FileService


logger = logging.getLogger(__name__)


class DocumentService:
    """Service for handling contract document operations"""

    @staticmethod
    def upload_document(contract_id, file, uploaded_by, document_type="contract", description=None, is_primary=False):
        """Upload a new document to a contract"""
        try:
            # Save file
            file_info = FileService.save_uploaded_file(file)
            
            # Extract text from document
            extracted_text = FileService.extract_text_from_file(
                file_info["file_path"], file_info["mime_type"]
            )
            
            # If setting as primary, unset other primary documents
            if is_primary:
                DocumentService._unset_primary_documents(contract_id)
            
            # Create document record
            document = ContractDocument(
                contract_id=contract_id,
                file_path=file_info["file_path"],
                file_name=file_info["filename"],
                original_filename=file.filename,
                file_size=file_info["file_size"],
                mime_type=file_info["mime_type"],
                extracted_text=extracted_text,
                document_type=document_type,
                description=description,
                uploaded_by=uploaded_by,
                is_primary=is_primary
            )
            
            db.session.add(document)
            db.session.commit()
            
            logger.info(f"Document uploaded: {file_info['filename']} to contract {contract_id}")
            return document
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading document to contract {contract_id}: {e}")
            raise

    @staticmethod
    def delete_document(document_id, contract_id=None):
        """Delete a document (hard delete)"""
        try:
            document = ContractDocument.query.get(document_id)
            
            if not document:
                raise ValueError("Document not found")
            
            # Verify contract ownership if provided
            if contract_id and document.contract_id != contract_id:
                raise ValueError("Document does not belong to specified contract")
            
            # Delete file from disk
            document.delete_file_from_disk()
            
            # If this was the primary document, set another document as primary
            if document.is_primary:
                DocumentService._set_next_primary_document(document.contract_id, exclude_id=document.id)
            
            # Delete from database
            db.session.delete(document)
            db.session.commit()
            
            logger.info(f"Document deleted: {document.file_name} from contract {document.contract_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting document {document_id}: {e}")
            raise

    @staticmethod
    def set_primary_document(document_id, contract_id):
        """Set a document as the primary document for a contract"""
        try:
            document = ContractDocument.query.filter_by(
                id=document_id, contract_id=contract_id
            ).first()
            
            if not document:
                raise ValueError("Document not found")
            
            # Unset other primary documents
            DocumentService._unset_primary_documents(contract_id)
            
            # Set this document as primary
            document.is_primary = True
            db.session.commit()
            
            logger.info(f"Document set as primary: {document.file_name} for contract {contract_id}")
            return document
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting primary document {document_id}: {e}")
            raise

    @staticmethod
    def get_contract_documents(contract_id):
        """Get all documents for a contract"""
        return ContractDocument.query.filter_by(contract_id=contract_id).order_by(
            ContractDocument.is_primary.desc(),
            ContractDocument.uploaded_at.desc()
        ).all()

    @staticmethod
    def get_document_by_id(document_id):
        """Get a document by ID"""
        return ContractDocument.query.get(document_id)

    @staticmethod
    def _unset_primary_documents(contract_id):
        """Helper method to unset all primary documents for a contract"""
        ContractDocument.query.filter_by(
            contract_id=contract_id, is_primary=True
        ).update({"is_primary": False})

    @staticmethod
    def _set_next_primary_document(contract_id, exclude_id=None):
        """Helper method to set the next document as primary when primary is deleted"""
        query = ContractDocument.query.filter_by(contract_id=contract_id)
        
        if exclude_id:
            query = query.filter(ContractDocument.id != exclude_id)
        
        next_document = query.order_by(ContractDocument.uploaded_at.desc()).first()
        
        if next_document:
            next_document.is_primary = True
            logger.info(f"Set {next_document.file_name} as new primary document for contract {contract_id}")

    @staticmethod
    def migrate_legacy_document(contract):
        """Migrate a contract's legacy single document to the new document system"""
        try:
            if not contract.file_path or not contract.file_name:
                return None
                
            # Check if already migrated
            existing_docs = DocumentService.get_contract_documents(contract.id)
            if existing_docs:
                return None  # Already has documents, skip migration
                
            # Create document record from legacy fields
            document = ContractDocument(
                contract_id=contract.id,
                file_path=contract.file_path,
                file_name=contract.file_name,
                original_filename=contract.file_name,  # Use file_name as original
                file_size=contract.file_size or 0,
                mime_type=contract.mime_type or "application/octet-stream",
                extracted_text=contract.extracted_text,
                document_type="contract",
                description="Migrated from legacy single document",
                uploaded_by=contract.created_by,
                uploaded_at=contract.created_at,
                is_primary=True
            )
            
            db.session.add(document)
            db.session.commit()
            
            logger.info(f"Migrated legacy document for contract {contract.id}: {contract.file_name}")
            return document
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error migrating legacy document for contract {contract.id}: {e}")
            raise
