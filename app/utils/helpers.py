"""
Helper utility functions for Contract Management Platform
"""
from datetime import datetime, date
import locale


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def format_currency(amount, currency="USD"):
    """Format currency amount"""
    if amount is None:
        return "N/A"

    try:
        locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        return locale.currency(amount, grouping=True)
    except:
        # Fallback formatting
        return f"${amount:,.2f}"


def format_date(date_obj, format_str="%Y-%m-%d"):
    """Format date object to string"""
    if not date_obj:
        return "N/A"

    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except:
            return date_obj

    return date_obj.strftime(format_str)


def format_datetime(datetime_obj, format_str="%Y-%m-%d %H:%M"):
    """Format datetime object to string"""
    if not datetime_obj:
        return "N/A"

    if isinstance(datetime_obj, str):
        try:
            datetime_obj = datetime.fromisoformat(datetime_obj.replace("Z", "+00:00"))
        except:
            return datetime_obj

    return datetime_obj.strftime(format_str)


def get_contract_status_display(status):
    """Get human readable contract status"""
    status_display = {
        "draft": "Draft",
        "under_review": "Under Review",
        "active": "Active",
        "expired": "Expired",
        "terminated": "Terminated",
        "renewed": "Renewed",
        "deleted": "Deleted",
    }

    return status_display.get(status, status.title().replace("_", " "))


def get_contract_status_color(status):
    """Get CSS color class for contract status"""
    status_colors = {
        "draft": "secondary",
        "under_review": "warning",
        "active": "success",
        "expired": "danger",
        "terminated": "dark",
        "renewed": "info",
        "deleted": "light",
    }

    return status_colors.get(status, "secondary")


def truncate_text(text, max_length=100):
    """Truncate text to specified length"""
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length].rsplit(" ", 1)[0] + "..."


def generate_pagination_info(pagination):
    """Generate pagination information for templates"""
    if not pagination:
        return {}

    return {
        "page": pagination.page,
        "pages": pagination.pages,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
        "next_num": pagination.next_num,
        "prev_num": pagination.prev_num,
    }


def get_days_until_expiry(expiration_date):
    """Calculate days until contract expiration"""
    if not expiration_date:
        return None

    if isinstance(expiration_date, str):
        try:
            expiration_date = datetime.strptime(expiration_date, "%Y-%m-%d").date()
        except:
            return None

    today = date.today()
    delta = expiration_date - today
    return delta.days


def is_expiring_soon(expiration_date, days=30):
    """Check if contract is expiring soon"""
    days_until = get_days_until_expiry(expiration_date)
    if days_until is None:
        return False

    return 0 <= days_until <= days
