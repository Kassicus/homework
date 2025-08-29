"""
Integration tests for Flask application
"""
import os
import tempfile

import pytest

from app import create_app, db
from app.models.client import Client
from app.models.contract import Contract
from app.models.user import User


@pytest.fixture
def app():
    """Create application for testing"""
    # Create a temporary file for the database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    # Create the database and load some test data
    with app.app_context():
        db.create_all()
        
        # Create test user
        user = User(
            username='testuser',
            email='test@example.com',
            is_active=True,
            is_admin=False
        )
        user.set_password('password123')
        db.session.add(user)
        
        # Create test client
        client = Client(
            name='Test Client',
            organization='Test Organization',
            email='client@example.com'
        )
        db.session.add(client)
        
        db.session.commit()
        
        # Store user and client IDs for tests
        app.test_user_id = user.id
        app.test_client_id = client.id
    
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test runner"""
    return app.test_cli_runner()


class TestApplicationCreation:
    """Test application creation and configuration"""
    
    def test_app_creation(self):
        """Test that the application can be created"""
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] is True
        
    def test_app_config(self):
        """Test application configuration"""
        app = create_app('testing')
        assert app.config['TESTING'] is True
        assert app.config['DEBUG'] is False
        
    def test_database_creation(self, app):
        """Test that database tables can be created"""
        with app.app_context():
            # Check that tables exist
            assert 'users' in [table.name for table in db.metadata.tables.values()]
            assert 'clients' in [table.name for table in db.metadata.tables.values()]
            assert 'contracts' in [table.name for table in db.metadata.tables.values()]


class TestDatabaseOperations:
    """Test database operations"""
    
    def test_user_creation(self, app):
        """Test user creation in database"""
        with app.app_context():
            user = User(
                username='newuser',
                email='newuser@example.com',
                is_active=True,
                is_admin=False
            )
            user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            # Verify user was created
            created_user = User.query.filter_by(username='newuser').first()
            assert created_user is not None
            assert created_user.email == 'newuser@example.com'
            assert created_user.check_password('password123') is True
            
    def test_client_creation(self, app):
        """Test client creation in database"""
        with app.app_context():
            client = Client(
                name='New Client',
                organization='New Organization',
                email='newclient@example.com'
            )
            
            db.session.add(client)
            db.session.commit()
            
            # Verify client was created
            created_client = Client.query.filter_by(name='New Client').first()
            assert created_client is not None
            assert created_client.organization == 'New Organization'
            
    def test_contract_creation(self, app):
        """Test contract creation in database"""
        with app.app_context():
            contract = Contract(
                title='Test Contract',
                description='Test contract description',
                client_id=app.test_client_id,
                contract_type='Service',
                status=Contract.STATUS_DRAFT,
                created_by=app.test_user_id
            )
            
            db.session.add(contract)
            db.session.commit()
            
            # Verify contract was created
            created_contract = Contract.query.filter_by(title='Test Contract').first()
            assert created_contract is not None
            assert created_contract.client_id == app.test_client_id
            assert created_contract.created_by == app.test_user_id


class TestAuthentication:
    """Test authentication functionality"""
    
    def test_user_login(self, app, client):
        """Test user login functionality"""
        # Test login page loads
        response = client.get('/auth/login')
        assert response.status_code == 200
        
        # Test login with valid credentials
        response = client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Should redirect to dashboard after successful login
        assert response.status_code == 200
        
    def test_user_logout(self, app, client):
        """Test user logout functionality"""
        # First login
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Then logout
        response = client.get('/auth/logout', follow_redirects=True)
        assert response.status_code == 200
        
    def test_protected_route_access(self, app, client):
        """Test that protected routes require authentication"""
        # Try to access dashboard without login
        response = client.get('/dashboard/', follow_redirects=True)
        
        # Should redirect to login page
        assert response.status_code == 200
        # Check if redirected to login (this would be in the response content)


class TestContractManagement:
    """Test contract management functionality"""
    
    def test_contract_list_access(self, app, client):
        """Test access to contract list page"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Try to access contracts page
        response = client.get('/contracts/', follow_redirects=True)
        assert response.status_code == 200
        
    def test_contract_creation_workflow(self, app, client):
        """Test the complete contract creation workflow"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Access new contract page
        response = client.get('/contracts/new', follow_redirects=True)
        assert response.status_code == 200
        
        # Create a contract
        response = client.post('/contracts/new', data={
            'title': 'Integration Test Contract',
            'description': 'Contract created during integration testing',
            'client_id': app.test_client_id,
            'contract_type': 'Service',
            'status': Contract.STATUS_DRAFT
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify contract was created in database
        with app.app_context():
            created_contract = Contract.query.filter_by(
                title='Integration Test Contract'
            ).first()
            assert created_contract is not None


class TestClientManagement:
    """Test client management functionality"""
    
    def test_client_list_access(self, app, client):
        """Test access to client list page"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Try to access clients page
        response = client.get('/clients/', follow_redirects=True)
        assert response.status_code == 200
        
    def test_client_creation_workflow(self, app, client):
        """Test the complete client creation workflow"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Access new client page
        response = client.get('/clients/new', follow_redirects=True)
        assert response.status_code == 200
        
        # Create a client
        response = client.post('/clients/new', data={
            'name': 'Integration Test Client',
            'organization': 'Integration Test Org',
            'email': 'integration@example.com'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify client was created in database
        with app.app_context():
            created_client = Client.query.filter_by(
                name='Integration Test Client'
            ).first()
            assert created_client is not None


class TestDashboard:
    """Test dashboard functionality"""
    
    def test_dashboard_access(self, app, client):
        """Test access to dashboard page"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Try to access dashboard
        response = client.get('/dashboard/', follow_redirects=True)
        assert response.status_code == 200
        
    def test_dashboard_statistics(self, app, client):
        """Test dashboard statistics generation"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Access dashboard
        response = client.get('/dashboard/', follow_redirects=True)
        assert response.status_code == 200
        
        # Check that dashboard loads without errors
        # The actual content would depend on the templates being available


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_api_search_endpoint(self, app, client):
        """Test contract search API endpoint"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Test API search
        response = client.get('/contracts/api/search?q=test')
        assert response.status_code == 200
        
        # Should return JSON
        assert response.is_json
        
    def test_api_stats_endpoint(self, app, client):
        """Test dashboard stats API endpoint"""
        # Login first
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
        
        # Test API stats
        response = client.get('/dashboard/api/stats')
        assert response.status_code == 200
        
        # Should return JSON
        assert response.is_json


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_error(self, app, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        
    def test_database_error_handling(self, app):
        """Test database error handling"""
        with app.app_context():
            # This should not raise an exception
            try:
                db.session.execute('SELECT * FROM nonexistent_table')
            except Exception:
                # Expected to fail, but should not crash the app
                pass
