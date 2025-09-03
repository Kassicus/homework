"""
Admin routes for Contract Management Platform
"""
import logging
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.logging_db import get_logging_session
from app.models.activity_log import ActivityLog, ContractVersion
from app.models.contract import Contract
from app.models.user import User
from app.services.activity_service import get_user_activity_summary
from app.utils.activity_decorators import admin_required

logger = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """Admin dashboard with analytics and user activity"""
    try:
        # Get dashboard data
        dashboard_data = get_admin_dashboard_data()
        return render_template("admin/dashboard.html", dashboard_data=dashboard_data)
    
    except Exception as e:
        logger.error(f"Error loading admin dashboard: {e}")
        flash("An error occurred while loading the admin dashboard.", "error")
        return redirect(url_for("dashboard.index"))


@admin_bp.route("/activity")
@login_required
@admin_required
def activity():
    """User activity logs with pagination"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 100, type=int)
        user_id = request.args.get("user_id", type=int)
        action = request.args.get("action")
        resource_type = request.args.get("resource_type")
        
        # Get activities using direct session
        session = get_logging_session()
        try:
            query = session.query(ActivityLog)
            
            if user_id:
                query = query.filter(ActivityLog.user_id == user_id)
            if action:
                query = query.filter(ActivityLog.action == action)
            if resource_type:
                query = query.filter(ActivityLog.resource_type == resource_type)
            
            # Order by timestamp descending
            query = query.order_by(ActivityLog.timestamp.desc())
            
            # Manual pagination
            total = query.count()
            activities_list = query.offset((page - 1) * per_page).limit(per_page).all()
            
            # Create a simple pagination object
            class SimplePagination:
                def __init__(self, items, page, per_page, total):
                    self.items = items
                    self.page = page
                    self.per_page = per_page
                    self.total = total
                    self.pages = (total + per_page - 1) // per_page
                    self.has_prev = page > 1
                    self.has_next = page < self.pages
                    self.prev_num = page - 1 if self.has_prev else None
                    self.next_num = page + 1 if self.has_next else None
                
                def iter_pages(self):
                    for num in range(max(1, self.page - 2), min(self.pages + 1, self.page + 3)):
                        yield num
            
            activities = SimplePagination(activities_list, page, per_page, total)
        finally:
            session.close()
        
        # Get users for filter dropdown
        users = User.query.order_by(User.username).all()
        
        return render_template(
            "admin/activity.html",
            activities=activities,
            users=users,
            current_filters={
                'user_id': user_id,
                'action': action,
                'resource_type': resource_type
            }
        )
    
    except Exception as e:
        logger.error(f"Error loading activity logs: {e}")
        flash("An error occurred while loading activity logs.", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/analytics")
@login_required
@admin_required
def analytics():
    """Contract analytics and statistics"""
    try:
        analytics_data = get_analytics_data()
        return render_template("admin/analytics.html", analytics_data=analytics_data)
    
    except Exception as e:
        logger.error(f"Error loading analytics: {e}")
        flash("An error occurred while loading analytics.", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/contracts")
@login_required
@admin_required
def contracts():
    """Admin contract view including soft-deleted contracts"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 100, type=int)
        show_deleted = request.args.get("show_deleted", False, type=bool)
        
        # Get contracts including deleted ones for admin
        from app.services.contract_service import ContractService
        contracts = ContractService.get_all_contracts(
            include_deleted=True, page=page, per_page=per_page
        )
        
        return render_template(
            "admin/contracts.html",
            contracts=contracts,
            show_deleted=show_deleted
        )
    
    except Exception as e:
        logger.error(f"Error loading admin contracts: {e}")
        flash("An error occurred while loading contracts.", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """User management"""
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 100, type=int)
        
        users = User.query.order_by(User.username).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template("admin/users.html", users=users)
    
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        flash("An error occurred while loading users.", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/users/<int:user_id>/toggle-admin", methods=["POST"])
@login_required
@admin_required
def toggle_admin(user_id):
    """Toggle admin status for a user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent removing admin from current user
        if user.id == current_user.id:
            flash("You cannot remove admin privileges from yourself.", "error")
            return redirect(url_for("admin.users"))
        
        user.is_admin = not user.is_admin
        
        from app import db
        db.session.commit()
        
        action = "granted" if user.is_admin else "revoked"
        flash(f"Admin privileges {action} for {user.username}.", "success")
        
        # Log the admin action
        from app.services.activity_service import log_user_activity
        log_user_activity(
            action="admin_toggle",
            resource_type="user",
            resource_id=user_id,
            resource_title=user.username,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error toggling admin status: {e}")
        flash("An error occurred while updating user privileges.", "error")
    
    return redirect(url_for("admin.users"))


def get_admin_dashboard_data():
    """Get data for admin dashboard"""
    try:
        # Get date ranges
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Basic statistics
        total_users = User.query.count()
        total_contracts = Contract.query.filter(Contract.deleted_at.is_(None)).count()
        deleted_contracts = Contract.query.filter(Contract.deleted_at.isnot(None)).count()
        
        # Get activity data using session
        session = get_logging_session()
        try:
            # Recent activity count
            recent_activity_count = session.query(ActivityLog).filter(
                ActivityLog.timestamp >= datetime.combine(week_ago, datetime.min.time())
            ).count()
            
            # Most viewed contracts (last 30 days)
            most_viewed = ActivityLog.get_most_viewed_resources(
                ActivityLog.RESOURCE_CONTRACT, limit=10, days=30
            )
            
            # Most active users (last 30 days)
            from sqlalchemy import func, desc
            most_active_users = (
                session.query(
                    ActivityLog.user_id,
                    func.count(ActivityLog.id).label("activity_count")
                )
                .filter(ActivityLog.timestamp >= datetime.combine(month_ago, datetime.min.time()))
                .group_by(ActivityLog.user_id)
                .order_by(desc("activity_count"))
                .limit(10)
                .all()
            )
        finally:
            session.close()
        
        # Get user details for most active users
        user_activity_data = []
        for user_id, count in most_active_users:
            user = User.query.get(user_id)
            if user:
                user_activity_data.append({
                    'user': user,
                    'activity_count': count
                })
        
        # Contract status distribution (using main db)
        from app import db
        status_distribution = (
            db.session.query(
                Contract.status,
                db.func.count(Contract.id).label("count")
            )
            .filter(Contract.deleted_at.is_(None))
            .group_by(Contract.status)
            .all()
        )
        
        return {
            'total_users': total_users,
            'total_contracts': total_contracts,
            'deleted_contracts': deleted_contracts,
            'recent_activity_count': recent_activity_count,
            'most_viewed_contracts': most_viewed,
            'most_active_users': user_activity_data,
            'status_distribution': status_distribution
        }
    
    except Exception as e:
        logger.error(f"Error getting admin dashboard data: {e}")
        return {}


def get_analytics_data():
    """Get analytics data for admin"""
    try:
        # Get date ranges
        today = datetime.utcnow().date()
        month_ago = today - timedelta(days=30)
        
        session = get_logging_session()
        try:
            from sqlalchemy import func
            
            # Activity by action type (last 30 days)
            activity_by_action = (
                session.query(
                    ActivityLog.action,
                    func.count(ActivityLog.id).label("count")
                )
                .filter(ActivityLog.timestamp >= datetime.combine(month_ago, datetime.min.time()))
                .group_by(ActivityLog.action)
                .all()
            )
            
            # Activity by resource type (last 30 days)
            activity_by_resource = (
                session.query(
                    ActivityLog.resource_type,
                    func.count(ActivityLog.id).label("count")
                )
                .filter(ActivityLog.timestamp >= datetime.combine(month_ago, datetime.min.time()))
                .group_by(ActivityLog.resource_type)
                .all()
            )
            
            # Daily activity for the last 30 days
            daily_activity = (
                session.query(
                    func.date(ActivityLog.timestamp).label("date"),
                    func.count(ActivityLog.id).label("count")
                )
                .filter(ActivityLog.timestamp >= datetime.combine(month_ago, datetime.min.time()))
                .group_by(func.date(ActivityLog.timestamp))
                .order_by("date")
                .all()
            )
        finally:
            session.close()
        
        return {
            'activity_by_action': activity_by_action,
            'activity_by_resource': activity_by_resource,
            'daily_activity': daily_activity
        }
    
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        return {}
