"""
Notification service for contract alerts and user notifications
"""
from datetime import datetime
import logging

from app import db
from app.models.contract import Contract


logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling notifications and alerts"""

    @staticmethod
    def check_expiring_contracts(days=30):
        """Check for contracts expiring soon and generate notifications"""
        try:
            from app.services.contract_service import ContractService

            expiring_contracts = ContractService.get_expiring_contracts(days)

            notifications = []

            for contract in expiring_contracts:
                days_until_expiry = contract.days_until_expiration()

                if days_until_expiry is not None:
                    notification = {
                        "type": "contract_expiring",
                        "contract_id": contract.id,
                        "contract_title": contract.title,
                        "client_name": contract.client.name
                        if contract.client
                        else "Unknown",
                        "days_until_expiry": days_until_expiry,
                        "expiration_date": contract.expiration_date,
                        "created_by": contract.created_by,
                        "created_at": datetime.utcnow(),
                    }

                    notifications.append(notification)

                    logger.info(
                        f"Expiration notification generated for contract: {contract.title} "
                        f"(expires in {days_until_expiry} days)"
                    )

            return notifications

        except Exception as e:
            logger.error(f"Error checking expiring contracts: {e}")
            raise

    @staticmethod
    def send_expiration_notifications():
        """Send notifications for expiring contracts"""
        try:
            notifications = NotificationService.check_expiring_contracts()

            for notification in notifications:
                # TODO: Implement email notification system
                # For now, just log the notification
                logger.info(
                    f"Notification: Contract '{notification['contract_title']}' "
                    f"expires in {notification['days_until_expiry']} days"
                )

                # TODO: Send email to contract creator and relevant users
                # TODO: Send email to client contacts if configured

            return len(notifications)

        except Exception as e:
            logger.error(f"Error sending expiration notifications: {e}")
            raise

    @staticmethod
    def send_status_change_notification(contract, old_status, new_status, changed_by):
        """Send notification when contract status changes"""
        try:
            notification = {
                "type": "status_change",
                "contract_id": contract.id,
                "contract_title": contract.title,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": changed_by.username if changed_by else "System",
                "changed_at": datetime.utcnow(),
                "client_name": contract.client.name if contract.client else "Unknown",
            }

            # TODO: Implement email notification system
            logger.info(
                f"Status change notification: Contract '{contract.title}' "
                f"status changed from {old_status} to {new_status} by {changed_by.username}"
            )

            # TODO: Send email to relevant users based on status change
            # TODO: Send email to client contacts for certain status changes

            return notification

        except Exception as e:
            logger.error(f"Error sending status change notification: {e}")
            raise

    @staticmethod
    def send_daily_summary():
        """Send daily summary of contract activities"""
        try:
            from app.services.contract_service import ContractService

            # Get today's statistics
            stats = ContractService.get_contract_statistics()

            # Get today's activities
            today = datetime.utcnow().date()

            # Count new contracts created today
            new_contracts = Contract.query.filter(
                db.func.date(Contract.created_at) == today
            ).count()

            # Count status changes today
            status_changes = (
                db.session.query(Contract)
                .join(Contract.status_history)
                .filter(db.func.date(Contract.status_history.any(changed_at=today)))
                .count()
            )

            summary = {
                "date": today,
                "total_contracts": stats["total_contracts"],
                "new_contracts_today": new_contracts,
                "status_changes_today": status_changes,
                "expiring_soon": stats["expiring_soon_count"],
                "total_value": stats["total_value"],
            }

            # TODO: Implement email notification system
            logger.info(
                f"Daily summary generated: {new_contracts} new contracts, "
                f"{status_changes} status changes, {stats['expiring_soon_count']} expiring soon"
            )

            # TODO: Send email to administrators
            # TODO: Send email to users who have contracts expiring soon

            return summary

        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")
            raise

    @staticmethod
    def send_weekly_report():
        """Send weekly contract management report"""
        try:
            from datetime import datetime, timedelta

            # Get date range for this week
            today = datetime.utcnow().date()
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)

            # Get weekly statistics
            weekly_stats = {
                "week_start": week_start,
                "week_end": week_end,
                "new_contracts": Contract.query.filter(
                    db.func.date(Contract.created_at).between(week_start, week_end)
                ).count(),
                "expired_contracts": Contract.query.filter(
                    db.func.date(Contract.expiration_date).between(week_start, week_end)
                ).count(),
                "status_changes": db.session.query(Contract)
                .join(Contract.status_history)
                .filter(
                    db.func.date(
                        Contract.status_history.any(
                            changed_at=db.func.date(week_start, week_end)
                        )
                    )
                )
                .count(),
            }

            # TODO: Implement email notification system
            logger.info(
                f"Weekly report generated: {weekly_stats['new_contracts']} new contracts, "
                f"{weekly_stats['expired_contracts']} expired, {weekly_stats['status_changes']} status changes"
            )

            # TODO: Send email to administrators and managers
            # TODO: Include charts and detailed breakdowns

            return weekly_stats

        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            raise

    @staticmethod
    def send_custom_notification(users, subject, message, notification_type="custom"):
        """Send custom notification to specific users"""
        try:
            if not users:
                logger.warning("No users specified for custom notification")
                return 0

            notification_count = 0

            for user in users:
                # TODO: Implement email notification system
                logger.info(f"Custom notification sent to {user.username}: {subject}")

                notification_count += 1

            return notification_count

        except Exception as e:
            logger.error(f"Error sending custom notifications: {e}")
            raise
