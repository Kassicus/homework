"""
Contract service for contract management operations
"""
import logging
from datetime import datetime, date, timedelta
from sqlalchemy import or_, and_, desc
from flask import current_app, request
from app import db
from app.models.contract import Contract, ContractStatusHistory, ContractAccessHistory
from app.models.client import Client
from app.models.user import User
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

class ContractService:
    """Service for handling contract operations"""
    
    @staticmethod
    def create_contract(contract_data, file=None, created_by=None):
        """Create a new contract"""
        try:
            # Save file if provided
            file_info = None
            extracted_text = ""
            
            if file:
                file_info = FileService.save_uploaded_file(file)
                # Extract text from uploaded document
                extracted_text = FileService.extract_text_from_file(
                    file_info['file_path'], 
                    file_info['mime_type']
                )
            
            # Create contract
            contract = Contract(
                title=contract_data['title'],
                description=contract_data.get('description'),
                client_id=contract_data['client_id'],
                contract_type=contract_data['contract_type'],
                status=contract_data.get('status', Contract.STATUS_DRAFT),
                contract_value=contract_data.get('contract_value'),
                file_path=file_info['file_path'] if file_info else None,
                file_name=file_info['filename'] if file_info else None,
                file_size=file_info['file_size'] if file_info else None,
                mime_type=file_info['mime_type'] if file_info else None,
                extracted_text=extracted_text,
                created_date=contract_data.get('created_date', date.today()),
                effective_date=contract_data.get('effective_date'),
                expiration_date=contract_data.get('expiration_date'),
                renewal_date=contract_data.get('renewal_date'),
                created_by=created_by
            )
            
            db.session.add(contract)
            db.session.commit()
            
            # Log contract creation
            logger.info(f"Contract created: {contract.title} by user {created_by}")
            
            return contract
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating contract: {e}")
            raise
    
    @staticmethod
    def get_contract_by_id(contract_id, include_deleted=False):
        """Get contract by ID"""
        try:
            query = Contract.query
            if not include_deleted:
                query = query.filter(Contract.deleted_at.is_(None))
            
            contract = query.get(contract_id)
            
            if contract:
                # Log access
                contract.log_access(
                    user_id=request.remote_user.id if hasattr(request, 'remote_user') else None,
                    access_type='view',
                    ip_address=request.remote_addr,
                    user_agent=request.user_agent.string
                )
                db.session.commit()
            
            return contract
            
        except Exception as e:
            logger.error(f"Error getting contract {contract_id}: {e}")
            raise
    
    @staticmethod
    def get_all_contracts(include_deleted=False, page=1, per_page=20):
        """Get all contracts with pagination"""
        try:
            query = Contract.query
            
            if not include_deleted:
                query = query.filter(Contract.deleted_at.is_(None))
            
            # Order by creation date (newest first)
            query = query.order_by(desc(Contract.created_at))
            
            # Pagination
            contracts = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error getting all contracts: {e}")
            raise
    
    @staticmethod
    def search_contracts(search_term, filters=None, page=1, per_page=20):
        """Search contracts by text and filters"""
        try:
            query = Contract.query.filter(Contract.deleted_at.is_(None))
            
            # Text search across title, description, and extracted text
            if search_term:
                search_filter = or_(
                    Contract.title.ilike(f'%{search_term}%'),
                    Contract.description.ilike(f'%{search_term}%'),
                    Contract.extracted_text.ilike(f'%{search_term}%')
                )
                query = query.filter(search_filter)
            
            # Apply filters
            if filters:
                if filters.get('status'):
                    query = query.filter(Contract.status == filters['status'])
                
                if filters.get('client_id'):
                    query = query.filter(Contract.client_id == filters['client_id'])
                
                if filters.get('contract_type'):
                    query = query.filter(Contract.contract_type == filters['contract_type'])
                
                if filters.get('date_from'):
                    query = query.filter(Contract.created_date >= filters['date_from'])
                
                if filters.get('date_to'):
                    query = query.filter(Contract.created_date <= filters['date_to'])
                
                if filters.get('expiring_soon'):
                    days = filters.get('expiring_soon', 30)
                    cutoff_date = date.today() + timedelta(days=days)
                    query = query.filter(
                        and_(
                            Contract.status == Contract.STATUS_ACTIVE,
                            Contract.expiration_date <= cutoff_date
                        )
                    )
            
            # Order by relevance (search term matches first) then by date
            if search_term:
                # Simple relevance scoring - contracts with search term in title get priority
                query = query.order_by(
                    Contract.title.ilike(f'%{search_term}%').desc(),
                    desc(Contract.created_at)
                )
            else:
                query = query.order_by(desc(Contract.created_at))
            
            # Pagination
            contracts = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error searching contracts: {e}")
            raise
    
    @staticmethod
    def update_contract(contract_id, update_data, updated_by=None):
        """Update contract information"""
        try:
            contract = ContractService.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError("Contract not found")
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(contract, field) and field not in ['id', 'created_at', 'created_by']:
                    setattr(contract, field, value)
            
            contract.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Contract updated: {contract.title} by user {updated_by}")
            return contract
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating contract {contract_id}: {e}")
            raise
    
    @staticmethod
    def update_contract_status(contract_id, new_status, changed_by, reason=None):
        """Update contract status and record in history"""
        try:
            contract = ContractService.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError("Contract not found")
            
            # Update status
            status_history = contract.update_status(new_status, changed_by.id, reason)
            db.session.commit()
            
            logger.info(f"Contract status updated: {contract.title} - {new_status}")
            return contract
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating contract status {contract_id}: {e}")
            raise
    
    @staticmethod
    def soft_delete_contract(contract_id, deleted_by):
        """Soft delete contract (mark as deleted but retain for 30 days)"""
        try:
            contract = ContractService.get_contract_by_id(contract_id)
            if not contract:
                raise ValueError("Contract not found")
            
            # Soft delete
            contract.soft_delete(deleted_by.id)
            db.session.commit()
            
            logger.info(f"Contract soft deleted: {contract.title} by user {deleted_by.username}")
            return contract
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error soft deleting contract {contract_id}: {e}")
            raise
    
    @staticmethod
    def restore_contract(contract_id, restored_by):
        """Restore soft-deleted contract"""
        try:
            contract = Contract.query.get(contract_id)
            if not contract:
                raise ValueError("Contract not found")
            
            if not contract.deleted_at:
                raise ValueError("Contract is not deleted")
            
            # Restore contract
            contract.restore(restored_by.id)
            db.session.commit()
            
            logger.info(f"Contract restored: {contract.title} by user {restored_by.username}")
            return contract
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error restoring contract {contract_id}: {e}")
            raise
    
    @staticmethod
    def get_contracts_by_status(status, include_deleted=False):
        """Get contracts by status"""
        try:
            query = Contract.query.filter(Contract.status == status)
            
            if not include_deleted:
                query = query.filter(Contract.deleted_at.is_(None))
            
            return query.order_by(desc(Contract.created_at)).all()
            
        except Exception as e:
            logger.error(f"Error getting contracts by status {status}: {e}")
            raise
    
    @staticmethod
    def get_expiring_contracts(days=30):
        """Get contracts expiring within specified days"""
        try:
            cutoff_date = date.today() + timedelta(days=days)
            
            contracts = Contract.query.filter(
                and_(
                    Contract.status == Contract.STATUS_ACTIVE,
                    Contract.expiration_date <= cutoff_date,
                    Contract.deleted_at.is_(None)
                )
            ).order_by(Contract.expiration_date).all()
            
            return contracts
            
        except Exception as e:
            logger.error(f"Error getting expiring contracts: {e}")
            raise
    
    @staticmethod
    def get_contract_statistics():
        """Get contract statistics for dashboard"""
        try:
            total_contracts = Contract.query.filter(Contract.deleted_at.is_(None)).count()
            
            status_counts = db.session.query(
                Contract.status, 
                db.func.count(Contract.id)
            ).filter(
                Contract.deleted_at.is_(None)
            ).group_by(Contract.status).all()
            
            expiring_soon = ContractService.get_expiring_contracts(30)
            
            # Calculate total contract value
            total_value = db.session.query(
                db.func.sum(Contract.contract_value)
            ).filter(
                and_(
                    Contract.deleted_at.is_(None),
                    Contract.contract_value.isnot(None)
                )
            ).scalar() or 0
            
            return {
                'total_contracts': total_contracts,
                'status_counts': dict(status_counts),
                'expiring_soon_count': len(expiring_soon),
                'total_value': float(total_value)
            }
            
        except Exception as e:
            logger.error(f"Error getting contract statistics: {e}")
            raise
    
    @staticmethod
    def cleanup_expired_deleted_contracts():
        """Clean up contracts that have been soft-deleted for more than 30 days"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Get expired deleted contracts
            expired_contracts = Contract.query.filter(
                and_(
                    Contract.deleted_at <= cutoff_date,
                    Contract.deleted_at.isnot(None)
                )
            ).all()
            
            deleted_count = 0
            
            for contract in expired_contracts:
                try:
                    # Delete associated file if it exists
                    if contract.file_path:
                        FileService.delete_file(contract.file_path)
                    
                    # Delete contract from database
                    db.session.delete(contract)
                    deleted_count += 1
                    
                    logger.info(f"Expired deleted contract permanently removed: {contract.title}")
                    
                except Exception as e:
                    logger.error(f"Error removing expired deleted contract {contract.id}: {e}")
            
            db.session.commit()
            logger.info(f"Cleanup completed: {deleted_count} expired deleted contracts removed")
            
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during expired deleted contracts cleanup: {e}")
            raise
