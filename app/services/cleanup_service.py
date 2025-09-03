"""
Cleanup service for managing data retention policies
"""
import logging
from datetime import datetime, timedelta
from threading import Timer

from app import db
from app.models.contract import Contract
from app.logging_db import cleanup_old_logs

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for automatic data cleanup"""
    
    def __init__(self):
        self.cleanup_timer = None
        self.running = False
    
    def start_scheduled_cleanup(self, interval_hours=24):
        """Start scheduled cleanup tasks"""
        if not self.running:
            self.running = True
            self._schedule_next_cleanup(interval_hours)
            logger.info(f"Cleanup service started with {interval_hours}h interval")
    
    def stop_scheduled_cleanup(self):
        """Stop scheduled cleanup tasks"""
        self.running = False
        if self.cleanup_timer:
            self.cleanup_timer.cancel()
            logger.info("Cleanup service stopped")
    
    def _schedule_next_cleanup(self, interval_hours):
        """Schedule the next cleanup run"""
        if self.running:
            self.cleanup_timer = Timer(
                interval_hours * 3600,  # Convert hours to seconds
                self._run_cleanup_and_reschedule,
                args=[interval_hours]
            )
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
    
    def _run_cleanup_and_reschedule(self, interval_hours):
        """Run cleanup and schedule next run"""
        try:
            self.run_all_cleanup_tasks()
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
        
        # Schedule next cleanup
        self._schedule_next_cleanup(interval_hours)
    
    def run_all_cleanup_tasks(self):
        """Run all cleanup tasks"""
        logger.info("Starting cleanup tasks...")
        
        # Clean up old activity logs (30 days)
        old_logs, old_versions = cleanup_old_logs(days=30)
        if old_logs > 0 or old_versions > 0:
            logger.info(f"Cleaned up {old_logs} old activity logs and {old_versions} old contract versions")
        
        # Clean up soft-deleted contracts (30 days)
        deleted_contracts = self.cleanup_soft_deleted_contracts(days=30)
        if deleted_contracts > 0:
            logger.info(f"Permanently deleted {deleted_contracts} soft-deleted contracts")
        
        logger.info("Cleanup tasks completed")
    
    def cleanup_soft_deleted_contracts(self, days=30):
        """Permanently delete contracts that have been soft-deleted for more than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Find contracts that have been soft-deleted for more than the cutoff period
            contracts_to_delete = Contract.query.filter(
                Contract.deleted_at.isnot(None),
                Contract.deleted_at < cutoff_date
            ).all()
            
            count = len(contracts_to_delete)
            
            if count > 0:
                # Log the contracts being permanently deleted
                for contract in contracts_to_delete:
                    logger.info(f"Permanently deleting contract: {contract.title} (ID: {contract.id})")
                
                # Delete the contracts
                for contract in contracts_to_delete:
                    db.session.delete(contract)
                
                db.session.commit()
                logger.info(f"Permanently deleted {count} soft-deleted contracts")
            
            return count
        
        except Exception as e:
            logger.error(f"Error cleaning up soft-deleted contracts: {e}")
            db.session.rollback()
            return 0
    
    def cleanup_expired_sessions(self, days=7):
        """Clean up expired user sessions (placeholder for future session management)"""
        # This would be implemented if we had a session table
        pass
    
    def get_cleanup_statistics(self):
        """Get statistics about data that can be cleaned up"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Count soft-deleted contracts ready for cleanup
            soft_deleted_count = Contract.query.filter(
                Contract.deleted_at.isnot(None),
                Contract.deleted_at < cutoff_date
            ).count()
            
            # Count recent soft-deleted contracts (not ready for cleanup yet)
            recent_soft_deleted = Contract.query.filter(
                Contract.deleted_at.isnot(None),
                Contract.deleted_at >= cutoff_date
            ).count()
            
            return {
                'soft_deleted_ready_for_cleanup': soft_deleted_count,
                'recent_soft_deleted': recent_soft_deleted,
                'cleanup_cutoff_date': cutoff_date
            }
        
        except Exception as e:
            logger.error(f"Error getting cleanup statistics: {e}")
            return {}


# Global cleanup service instance
cleanup_service = CleanupService()
