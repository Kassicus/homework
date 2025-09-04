"""
DocuSign Mock Service for Contract Management Platform
This is a proof-of-concept implementation that simulates DocuSign integration
without requiring actual DocuSign accounts or API setup.
"""
import logging
import random
import uuid
from datetime import datetime, timedelta

from app import db
from app.models.contract import Contract
from app.utils.activity_decorators import log_update
from app.services.activity_service import log_user_activity
from app.models.activity_log import ActivityLog

logger = logging.getLogger(__name__)


class DocuSignMockService:
    """
    Mock DocuSign service for demonstration purposes.
    Simulates all DocuSign API functionality without external dependencies.
    """
    
    # Mock DocuSign statuses that we'll cycle through
    MOCK_STATUSES = [
        'sent',
        'delivered', 
        'completed',
        'declined',
        'voided'
    ]
    
    # Realistic envelope ID format
    ENVELOPE_ID_PREFIX = "mock-ds-"
    
    def __init__(self):
        """Initialize mock service"""
        self.is_mock_mode = True
        logger.info("DocuSign Mock Service initialized - PROOF OF CONCEPT MODE")
    
    def send_contract_for_signature(self, contract_id, recipient_email, recipient_name=None, document_id=None):
        """
        Mock sending contract to client for signature
        Simulates DocuSign envelope creation and sending
        """
        try:
            contract = Contract.query.get_or_404(contract_id)
            
            # Validate inputs
            if not recipient_email or '@' not in recipient_email:
                return {
                    'success': False,
                    'error': 'Valid recipient email is required'
                }
            
            # Validate and get selected document
            if document_id:
                from app.models.contract_document import ContractDocument
                selected_document = ContractDocument.query.filter_by(
                    id=document_id, 
                    contract_id=contract_id
                ).first()
                
                if not selected_document:
                    return {
                        'success': False,
                        'error': 'Selected document not found or does not belong to this contract'
                    }
            else:
                # Fallback to primary document or first available document
                selected_document = contract.get_primary_document()
                if not selected_document:
                    selected_document = contract.documents.first()
                
                if not selected_document and not contract.file_path:
                    return {
                        'success': False,
                        'error': 'No documents available to send'
                    }
            
            # Generate mock envelope ID (realistic format)
            mock_envelope_id = f"{self.ENVELOPE_ID_PREFIX}{uuid.uuid4().hex[:16]}"
            
            # Simulate API call delay (realistic timing)
            import time
            time.sleep(0.5)  # Simulate network delay
            
            # Simulate occasional API errors for realism (5% chance)
            if random.random() < 0.05:
                logger.warning(f"Mock DocuSign API error for contract {contract_id}")
                return {
                    'success': False,
                    'error': 'DocuSign service temporarily unavailable (mock error)'
                }
            
            # Update contract with mock DocuSign data
            contract.docusign_envelope_id = mock_envelope_id
            contract.docusign_status = 'sent'
            contract.docusign_sent_date = datetime.utcnow()
            contract.docusign_recipient_email = recipient_email
            contract.docusign_recipient_name = recipient_name or contract.client.name
            contract.docusign_document_id = selected_document.id if selected_document else None
            
            # Update contract status to under_review when sent for signature
            if contract.status == Contract.STATUS_DRAFT:
                contract.status = Contract.STATUS_UNDER_REVIEW
            
            db.session.commit()
            
            # Log the activity with document information
            document_info = f"{selected_document.original_filename} ({selected_document.get_file_size_human()})" if selected_document else "Legacy document"
            
            # Log detailed DocuSign send activity
            try:
                log_user_activity(
                    action=ActivityLog.ACTION_DOCUSIGN_SEND,
                    resource_type=ActivityLog.RESOURCE_CONTRACT,
                    resource_id=contract_id,
                    resource_title=f"{contract.title} (Envelope: {mock_envelope_id[:8]}...)",
                    success=True,
                    additional_data={
                        'envelope_id': mock_envelope_id,
                        'recipient_email': recipient_email,
                        'recipient_name': recipient_name,
                        'document_name': selected_document.original_filename if selected_document else None,
                        'document_size': selected_document.get_file_size_human() if selected_document else None,
                        'document_id': selected_document.id if selected_document else None,
                        'mock_service': True
                    }
                )
            except Exception as log_error:
                logger.warning(f"Failed to log DocuSign send activity: {log_error}")
            
            logger.info(f"[MOCK] Contract {contract_id} sent to DocuSign. Envelope ID: {mock_envelope_id}")
            logger.info(f"[MOCK] Document: {document_info}")
            logger.info(f"[MOCK] Recipient: {recipient_email} ({recipient_name})")
            
            return {
                'success': True,
                'envelope_id': mock_envelope_id,
                'status': 'sent',
                'message': f'Contract successfully sent to {recipient_email} for signature',
                'mock_mode': True
            }
            
        except Exception as e:
            logger.error(f"Error in mock DocuSign send: {e}")
            return {
                'success': False,
                'error': f'Failed to send contract: {str(e)}'
            }
    
    def check_envelope_status(self, envelope_id, contract_id=None):
        """
        Mock checking DocuSign envelope status
        Simulates realistic status progression over time
        """
        try:
            if not envelope_id.startswith(self.ENVELOPE_ID_PREFIX):
                return {
                    'success': False,
                    'error': 'Invalid envelope ID format'
                }
            
            # Get contract if ID provided
            contract = None
            if contract_id:
                contract = Contract.query.get(contract_id)
            elif envelope_id:
                contract = Contract.query.filter_by(docusign_envelope_id=envelope_id).first()
            
            if not contract:
                return {
                    'success': False,
                    'error': 'Contract not found for envelope'
                }
            
            # Simulate status progression based on time elapsed
            sent_date = contract.docusign_sent_date
            if not sent_date:
                return {
                    'success': False,
                    'error': 'No send date found for envelope'
                }
            
            time_elapsed = datetime.utcnow() - sent_date
            current_status = contract.docusign_status
            
            # Simulate realistic status progression
            new_status = self._simulate_status_progression(current_status, time_elapsed)
            
            # Update status if it changed
            if new_status != current_status:
                old_status = current_status
                contract.docusign_status = new_status
                
                # Set completion date if completed
                if new_status == 'completed' and not contract.docusign_completed_date:
                    contract.docusign_completed_date = datetime.utcnow()
                    # Update contract status to active when signed
                    if contract.status == Contract.STATUS_UNDER_REVIEW:
                        contract.status = Contract.STATUS_ACTIVE
                
                db.session.commit()
                
                # Log the status change activity
                try:
                    log_user_activity(
                        action=ActivityLog.ACTION_DOCUSIGN_STATUS_CHANGE,
                        resource_type=ActivityLog.RESOURCE_CONTRACT,
                        resource_id=contract_id,
                        resource_title=f"{contract.title} (Envelope: {envelope_id[:8]}...)",
                        success=True,
                        additional_data={
                            'old_status': old_status,
                            'new_status': new_status,
                            'envelope_id': envelope_id,
                            'mock_service': True
                        }
                    )
                except Exception as log_error:
                    logger.warning(f"Failed to log DocuSign status change: {log_error}")
                
                logger.info(f"[MOCK] Envelope {envelope_id} status updated to: {new_status}")
            
            return {
                'success': True,
                'envelope_id': envelope_id,
                'status': new_status,
                'sent_date': sent_date.isoformat() if sent_date else None,
                'completed_date': contract.docusign_completed_date.isoformat() if contract.docusign_completed_date else None,
                'recipient_email': contract.docusign_recipient_email,
                'recipient_name': contract.docusign_recipient_name,
                'mock_mode': True,
                'message': self._get_status_message(new_status)
            }
            
        except Exception as e:
            logger.error(f"Error checking mock envelope status: {e}")
            return {
                'success': False,
                'error': f'Failed to check status: {str(e)}'
            }
    
    def _simulate_status_progression(self, current_status, time_elapsed):
        """
        Simulate realistic DocuSign status progression over time
        """
        minutes_elapsed = time_elapsed.total_seconds() / 60
        
        # Simulate realistic timing
        if current_status == 'sent':
            if minutes_elapsed > 2:  # After 2 minutes, mark as delivered
                return 'delivered'
        elif current_status == 'delivered':
            if minutes_elapsed > 5:  # After 5 minutes, randomly complete or keep delivered
                # 70% chance of completion, 20% still delivered, 10% declined
                rand = random.random()
                if rand < 0.7:
                    return 'completed'
                elif rand < 0.9:
                    return 'delivered'  # Still waiting
                else:
                    return 'declined'
        
        return current_status
    
    def _get_status_message(self, status):
        """Get user-friendly status message"""
        status_messages = {
            'sent': 'Document has been sent to recipient',
            'delivered': 'Recipient has received the document',
            'completed': 'Document has been signed and completed',
            'declined': 'Recipient has declined to sign',
            'voided': 'Document has been voided'
        }
        return status_messages.get(status, f'Status: {status}')
    
    def get_envelope_documents(self, envelope_id):
        """
        Mock getting signed documents from DocuSign
        In real implementation, this would download the signed PDF
        """
        try:
            contract = Contract.query.filter_by(docusign_envelope_id=envelope_id).first()
            if not contract:
                return {
                    'success': False,
                    'error': 'Contract not found'
                }
            
            # In mock mode, we'll just return the original document info
            return {
                'success': True,
                'envelope_id': envelope_id,
                'documents': [
                    {
                        'document_id': '1',
                        'name': f'signed_{contract.title}.pdf',
                        'type': 'content',
                        'status': contract.docusign_status
                    }
                ],
                'mock_mode': True,
                'message': 'In production, this would download the signed PDF from DocuSign'
            }
            
        except Exception as e:
            logger.error(f"Error getting mock envelope documents: {e}")
            return {
                'success': False,
                'error': f'Failed to get documents: {str(e)}'
            }
    
    def bulk_send_contracts(self, contract_ids, recipient_emails):
        """
        Mock bulk sending multiple contracts
        """
        try:
            results = []
            
            for i, contract_id in enumerate(contract_ids):
                if i < len(recipient_emails):
                    result = self.send_contract_for_signature(
                        contract_id, 
                        recipient_emails[i],
                        f"Recipient {i+1}"
                    )
                    results.append({
                        'contract_id': contract_id,
                        'result': result
                    })
            
            successful = len([r for r in results if r['result']['success']])
            
            return {
                'success': True,
                'total_sent': successful,
                'total_attempted': len(contract_ids),
                'results': results,
                'mock_mode': True
            }
            
        except Exception as e:
            logger.error(f"Error in mock bulk send: {e}")
            return {
                'success': False,
                'error': f'Bulk send failed: {str(e)}'
            }
    
    @staticmethod
    def get_docusign_status_badge_class(status):
        """Get Bootstrap badge class for DocuSign status"""
        status_classes = {
            'sent': 'bg-info',
            'delivered': 'bg-warning',
            'completed': 'bg-success',
            'declined': 'bg-danger',
            'voided': 'bg-secondary'
        }
        return status_classes.get(status, 'bg-light')
    
    @staticmethod
    def get_docusign_status_icon(status):
        """Get Bootstrap icon for DocuSign status"""
        status_icons = {
            'sent': 'bi-send',
            'delivered': 'bi-envelope-open',
            'completed': 'bi-check-circle-fill',
            'declined': 'bi-x-circle-fill',
            'voided': 'bi-slash-circle'
        }
        return status_icons.get(status, 'bi-question-circle')
    
    def populate_existing_contracts_with_mock_data(self):
        """
        Populate existing contracts with realistic DocuSign statuses
        based on their current contract status
        """
        try:
            contracts = Contract.query.filter(Contract.deleted_at.is_(None)).all()
            updated_count = 0
            
            for contract in contracts:
                # Skip contracts that already have DocuSign data
                if contract.docusign_envelope_id:
                    continue
                
                # Determine DocuSign status based on contract status
                docusign_status = None
                docusign_envelope_id = None
                docusign_sent_date = None
                docusign_completed_date = None
                
                if contract.status == Contract.STATUS_ACTIVE:
                    # Active contracts should show as completed (signed)
                    docusign_status = 'completed'
                    docusign_envelope_id = f"{self.ENVELOPE_ID_PREFIX}{uuid.uuid4().hex[:16]}"
                    # Set sent date to a few days ago
                    docusign_sent_date = contract.created_at - timedelta(days=random.randint(1, 7))
                    # Set completed date between sent date and now
                    docusign_completed_date = docusign_sent_date + timedelta(hours=random.randint(2, 48))
                    
                elif contract.status == Contract.STATUS_TERMINATED:
                    # Terminated contracts were completed but then terminated
                    docusign_status = 'completed'
                    docusign_envelope_id = f"{self.ENVELOPE_ID_PREFIX}{uuid.uuid4().hex[:16]}"
                    docusign_sent_date = contract.created_at - timedelta(days=random.randint(7, 30))
                    docusign_completed_date = docusign_sent_date + timedelta(hours=random.randint(2, 72))
                    
                elif contract.status == Contract.STATUS_UNDER_REVIEW:
                    # Under review contracts are sent but not yet confirmed (delivered or sent)
                    statuses = ['sent', 'delivered']
                    docusign_status = random.choice(statuses)
                    docusign_envelope_id = f"{self.ENVELOPE_ID_PREFIX}{uuid.uuid4().hex[:16]}"
                    docusign_sent_date = contract.created_at + timedelta(hours=random.randint(1, 24))
                    
                elif contract.status == Contract.STATUS_DRAFT:
                    # Draft contracts should not have DocuSign data (unsigned)
                    continue
                    
                elif contract.status == Contract.STATUS_EXPIRED:
                    # Some expired contracts might have been completed, others not
                    if random.random() < 0.7:  # 70% were completed before expiring
                        docusign_status = 'completed'
                        docusign_envelope_id = f"{self.ENVELOPE_ID_PREFIX}{uuid.uuid4().hex[:16]}"
                        docusign_sent_date = contract.created_at - timedelta(days=random.randint(30, 90))
                        docusign_completed_date = docusign_sent_date + timedelta(hours=random.randint(2, 168))
                    else:  # 30% were sent but never completed
                        docusign_status = random.choice(['sent', 'delivered'])
                        docusign_envelope_id = f"{self.ENVELOPE_ID_PREFIX}{uuid.uuid4().hex[:16]}"
                        docusign_sent_date = contract.created_at - timedelta(days=random.randint(30, 90))
                
                # Update contract with mock DocuSign data
                if docusign_status:
                    contract.docusign_envelope_id = docusign_envelope_id
                    contract.docusign_status = docusign_status
                    contract.docusign_sent_date = docusign_sent_date
                    contract.docusign_completed_date = docusign_completed_date
                    
                    # Set recipient info from client if available
                    if contract.client:
                        contract.docusign_recipient_email = contract.client.email or f"client{contract.client.id}@example.com"
                        contract.docusign_recipient_name = contract.client.name
                    else:
                        contract.docusign_recipient_email = f"client{contract.id}@example.com"
                        contract.docusign_recipient_name = f"Client {contract.id}"
                    
                    updated_count += 1
            
            db.session.commit()
            logger.info(f"[MOCK] Populated {updated_count} contracts with realistic DocuSign statuses")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'message': f'Successfully populated {updated_count} contracts with mock DocuSign data'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error populating contracts with mock DocuSign data: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance for easy import
docusign_service = DocuSignMockService()
