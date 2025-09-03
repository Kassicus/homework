"""
Logging database configuration for activity tracking
"""
import os
from flask import Flask
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create separate database components for logging
LoggingBase = declarative_base()
logging_engine = None
LoggingSession = None
logging_db_path = None


def init_logging_db(app: Flask):
    """Initialize logging database"""
    global logging_engine, LoggingSession, logging_db_path
    
    # Configure logging database path
    logging_db_path = os.path.join(app.instance_path, 'logs.db')
    logging_db_uri = f'sqlite:///{logging_db_path}'
    
    # Ensure instance directory exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Create engine and session factory
    logging_engine = create_engine(logging_db_uri, echo=False)
    LoggingSession = sessionmaker(bind=logging_engine)
    
    # Store in app config for access
    app.config['LOGGING_DATABASE_URI'] = logging_db_uri
    app.config['LOGGING_ENGINE'] = logging_engine
    app.config['LOGGING_SESSION'] = LoggingSession
    
    return logging_engine


def create_logging_tables(app: Flask):
    """Create logging database tables"""
    global logging_engine
    
    with app.app_context():
        # Import models to register them with LoggingBase
        from app.models.activity_log import ActivityLog, ContractVersion
        
        # Create all logging tables
        LoggingBase.metadata.create_all(logging_engine)
        print("✓ Logging database tables created successfully")


def get_logging_session():
    """Get a new logging database session"""
    if LoggingSession:
        return LoggingSession()
    return None


def cleanup_old_logs(days=30):
    """Clean up old activity logs and contract versions"""
    from datetime import datetime, timedelta
    from app.models.activity_log import ActivityLog, ContractVersion
    
    session = get_logging_session()
    if not session:
        return 0, 0
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Clean up old activity logs
        old_logs = session.query(ActivityLog).filter(ActivityLog.timestamp < cutoff_date).count()
        session.query(ActivityLog).filter(ActivityLog.timestamp < cutoff_date).delete()
        
        # Clean up old contract versions (keep longer - 90 days)
        version_cutoff = datetime.utcnow() - timedelta(days=90)
        old_versions = session.query(ContractVersion).filter(ContractVersion.timestamp < version_cutoff).count()
        session.query(ContractVersion).filter(ContractVersion.timestamp < version_cutoff).delete()
        
        session.commit()
        return old_logs, old_versions
        
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
