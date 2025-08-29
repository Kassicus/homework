"""
Database initialization script for Contract Management Platform
"""
import os
import sys
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.user import User
from app.models.client import Client
from app.models.contract import Contract, ContractStatusHistory, ContractAccessHistory

def init_database():
    """Initialize the database with schema and sample data"""
    app = create_app('development')
    
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables
        db.create_all()
        print("✓ Database tables created successfully")
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            print("Creating initial admin user...")
            
            # Create admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                is_active=True,
                is_admin=True
            )
            admin_user.set_password('admin123')
            
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Admin user created: admin/admin123")
        else:
            print("✓ Admin user already exists")
        
        # Check if sample clients exist
        if Client.query.count() == 0:
            print("Creating sample clients...")
            
            # Create sample clients
            clients = [
                Client(
                    name='Acme Corporation',
                    organization='Acme Corp',
                    email='contracts@acme.com',
                    phone='+1-555-0101',
                    address='123 Business St, City, State 12345'
                ),
                Client(
                    name='Tech Solutions Inc',
                    organization='Tech Solutions',
                    email='legal@techsolutions.com',
                    phone='+1-555-0102',
                    address='456 Innovation Ave, Tech City, TC 67890'
                ),
                Client(
                    name='Global Services Ltd',
                    organization='Global Services',
                    email='procurement@globalservices.com',
                    phone='+1-555-0103',
                    address='789 Corporate Blvd, Metro City, MC 11111'
                )
            ]
            
            for client in clients:
                db.session.add(client)
            
            db.session.commit()
            print(f"✓ {len(clients)} sample clients created")
        else:
            print("✓ Sample clients already exist")
        
        # Check if sample contracts exist
        if Contract.query.count() == 0:
            print("Creating sample contracts...")
            
            # Get the first client for sample contracts
            client = Client.query.first()
            if not client:
                print("No clients found. Please create clients first.")
                return
            
            # Create sample contracts
            contracts = [
                Contract(
                    title='Software License Agreement',
                    description='Annual software license for enterprise applications',
                    client_id=client.id,
                    contract_type='Software License',
                    status=Contract.STATUS_ACTIVE,
                    contract_value=50000.00,
                    created_date=date.today() - timedelta(days=30),
                    effective_date=date.today() - timedelta(days=30),
                    expiration_date=date.today() + timedelta(days=335),
                    created_by=admin_user.id
                ),
                Contract(
                    title='Consulting Services Contract',
                    description='Professional consulting services for Q1 2025',
                    client_id=client.id,
                    contract_type='Consulting',
                    status=Contract.STATUS_UNDER_REVIEW,
                    contract_value=25000.00,
                    created_date=date.today() - timedelta(days=15),
                    effective_date=date.today() + timedelta(days=15),
                    expiration_date=date.today() + timedelta(days=105),
                    created_by=admin_user.id
                ),
                Contract(
                    title='Equipment Purchase Agreement',
                    description='Purchase of new office equipment and furniture',
                    client_id=client.id,
                    contract_type='Purchase',
                    status=Contract.STATUS_DRAFT,
                    contract_value=15000.00,
                    created_date=date.today() - timedelta(days=5),
                    created_by=admin_user.id
                )
            ]
            
            for contract in contracts:
                db.session.add(contract)
            
            db.session.commit()
            print(f"✓ {len(contracts)} sample contracts created")
        else:
            print("✓ Sample contracts already exist")
        
        print("\nDatabase initialization completed successfully!")
        print("\nYou can now:")
        print("1. Run the development server: python run.py")
        print("2. Access the application at: http://localhost:5000")
        print("3. Login with: admin/admin123")

def reset_database():
    """Reset the database (drop all tables and recreate)"""
    app = create_app('development')
    
    with app.app_context():
        print("WARNING: This will delete all data!")
        confirm = input("Are you sure you want to reset the database? (yes/no): ")
        
        if confirm.lower() == 'yes':
            print("Dropping all tables...")
            db.drop_all()
            print("✓ All tables dropped")
            
            print("Recreating database...")
            init_database()
        else:
            print("Database reset cancelled.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        init_database()
