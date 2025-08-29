"""
Dashboard routes for Contract Management Platform
"""
import logging
from datetime import datetime, timedelta

from flask import Blueprint, render_template, current_app, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models.contract import Contract, ContractStatusHistory, ContractAccessHistory
from app.models.client import Client
from app.models.user import User
from app.services.contract_service import ContractService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page"""
    try:
        # Get contract statistics
        stats = ContractService.get_contract_statistics()
        
        # Get recent contracts
        recent_contracts = Contract.query.filter(
            Contract.deleted_at.is_(None)
        ).order_by(Contract.created_at.desc()).limit(5).all()
        
        # Get expiring contracts
        expiring_contracts = ContractService.get_expiring_contracts(30)
        
        # Get recent activity (status changes)
        recent_activity = ContractStatusHistory.query.order_by(
            ContractStatusHistory.changed_at.desc()
        ).limit(10).all()
        
        # Get user's contracts
        user_contracts = Contract.query.filter(
            Contract.created_by == current_user.id,
            Contract.deleted_at.is_(None)
        ).order_by(Contract.created_at.desc()).limit(5).all()
        
        # Get client count
        client_count = Client.query.count()
        
        # Get user count
        user_count = User.query.filter_by(is_active=True).count()
        
        dashboard_data = {
            'stats': stats,
            'recent_contracts': recent_contracts,
            'expiring_contracts': expiring_contracts,
            'recent_activity': recent_activity,
            'user_contracts': user_contracts,
            'client_count': client_count,
            'user_count': user_count
        }
        
        return render_template('dashboard/index.html', dashboard_data=dashboard_data)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('dashboard/index.html', dashboard_data=None)

@dashboard_bp.route('/contracts')
@login_required
def contracts():
    """Contracts overview dashboard"""
    try:
        # Get contracts by status
        status_counts = {}
        for status in Contract.VALID_STATUSES:
            count = Contract.query.filter(
                Contract.status == status,
                Contract.deleted_at.is_(None)
            ).count()
            status_counts[status] = count
        
        # Get contracts by month (last 12 months)
        monthly_contracts = []
        for i in range(12):
            date = datetime.now() - timedelta(days=30*i)
            month_start = date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            count = Contract.query.filter(
                func.date(Contract.created_at).between(month_start.date(), month_end.date()),
                Contract.deleted_at.is_(None)
            ).count()
            
            monthly_contracts.append({
                'month': month_start.strftime('%B %Y'),
                'count': count
            })
        
        monthly_contracts.reverse()  # Show oldest to newest
        
        # Get top clients by contract count
        top_clients = db.session.query(
            Client.name,
            func.count(Contract.id).label('contract_count')
        ).join(Contract).filter(
            Contract.deleted_at.is_(None)
        ).group_by(Client.id, Client.name).order_by(
            func.count(Contract.id).desc()
        ).limit(10).all()
        
        contracts_data = {
            'status_counts': status_counts,
            'monthly_contracts': monthly_contracts,
            'top_clients': top_clients
        }
        
        return render_template('dashboard/contracts.html', contracts_data=contracts_data)
        
    except Exception as e:
        logger.error(f"Error loading contracts dashboard: {e}")
        return render_template('dashboard/contracts.html', contracts_data=None)

@dashboard_bp.route('/reports')
@login_required
def reports():
    """Reports dashboard"""
    try:
        # Get contract value summary
        value_summary = db.session.query(
            func.sum(Contract.contract_value).label('total_value'),
            func.avg(Contract.contract_value).label('avg_value'),
            func.min(Contract.contract_value).label('min_value'),
            func.max(Contract.contract_value).label('max_value')
        ).filter(
            Contract.deleted_at.is_(None),
            Contract.contract_value.isnot(None)
        ).first()
        
        # Get contracts by type
        contracts_by_type = db.session.query(
            Contract.contract_type,
            func.count(Contract.id).label('count')
        ).filter(
            Contract.deleted_at.is_(None)
        ).group_by(Contract.contract_type).order_by(
            func.count(Contract.id).desc()
        ).all()
        
        # Get expiration analysis
        expiring_analysis = {
            'expired': Contract.query.filter(
                Contract.status == Contract.STATUS_EXPIRED,
                Contract.deleted_at.is_(None)
            ).count(),
            'expiring_30_days': ContractService.get_expiring_contracts(30),
            'expiring_60_days': ContractService.get_expiring_contracts(60),
            'expiring_90_days': ContractService.get_expiring_contracts(90)
        }
        
        reports_data = {
            'value_summary': value_summary,
            'contracts_by_type': contracts_by_type,
            'expiring_analysis': expiring_analysis
        }
        
        return render_template('dashboard/reports.html', reports_data=reports_data)
        
    except Exception as e:
        logger.error(f"Error loading reports dashboard: {e}")
        return render_template('dashboard/reports.html', reports_data=None)

@dashboard_bp.route('/activity')
@login_required
def activity():
    """Activity feed dashboard"""
    try:
        # Get recent status changes
        status_changes = ContractStatusHistory.query.order_by(
            ContractStatusHistory.changed_at.desc()
        ).limit(50).all()
        
        # Get recent access logs
        access_logs = ContractAccessHistory.query.order_by(
            ContractAccessHistory.accessed_at.desc()
        ).limit(50).all()
        
        # Get user activity summary
        user_activity = db.session.query(
            User.username,
            func.count(Contract.id).label('contracts_created'),
            func.max(Contract.created_at).label('last_activity')
        ).outerjoin(Contract, User.id == Contract.created_by).filter(
            User.is_active == True
        ).group_by(User.id, User.username).order_by(
            func.count(Contract.id).desc()
        ).all()
        
        activity_data = {
            'status_changes': status_changes,
            'access_logs': access_logs,
            'user_activity': user_activity
        }
        
        return render_template('dashboard/activity.html', activity_data=activity_data)
        
    except Exception as e:
        logger.error(f"Error loading activity dashboard: {e}")
        return render_template('dashboard/activity.html', activity_data=None)

@dashboard_bp.route('/notifications')
@login_required
def notifications():
    """Notifications dashboard"""
    try:
        # Get expiring contract notifications
        expiring_notifications = NotificationService.check_expiring_contracts(30)
        
        # Get recent system notifications (placeholder for future email system)
        system_notifications = []
        
        notifications_data = {
            'expiring_notifications': expiring_notifications,
            'system_notifications': system_notifications
        }
        
        return render_template('dashboard/notifications.html', notifications_data=notifications_data)
        
    except Exception as e:
        logger.error(f"Error loading notifications dashboard: {e}")
        return render_template('dashboard/notifications.html', notifications_data=None)

@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        stats = ContractService.get_contract_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return jsonify({'error': 'Failed to get statistics'}), 500

@dashboard_bp.route('/api/expiring')
@login_required
def api_expiring():
    """API endpoint for expiring contracts"""
    try:
        days = request.args.get('days', 30, type=int)
        expiring_contracts = ContractService.get_expiring_contracts(days)
        
        results = []
        for contract in expiring_contracts:
            results.append(contract.to_dict())
        
        return jsonify({
            'expiring_contracts': results,
            'days': days
        })
        
    except Exception as e:
        logger.error(f"Error getting expiring contracts API: {e}")
        return jsonify({'error': 'Failed to get expiring contracts'}), 500
