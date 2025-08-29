"""
Unit tests for database models
"""
import pytest
from datetime import datetime, date, timedelta
from app import create_app, db
from app.models.user import User
from app.models.client import Client
from app.models.contract import Contract, ContractStatusHistory, ContractAccessHistory


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app('testing')
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        db.create_all()
        yield db.session
        db.drop_all()


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self, db_session):
        """Test user creation"""
        user = User(
            username='testuser',
            email='test@example.com',
            is_active=True,
            is_admin=False
        )
        user.set_password('password123')
        
        db_session.add(user)
        db_session.commit()
        
        assert user.id is not None
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert user.is_active is True
        assert user.is_admin is False
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False
        
    def test_user_repr(self, db_session):
        """Test user string representation"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        
        assert repr(user) == '<User testuser>'
        
    def test_user_to_dict(self, db_session):
        """Test user to dictionary conversion"""
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        
        user_dict = user.to_dict()
        
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert 'password_hash' not in user_dict


class TestClientModel:
    """Test Client model functionality"""
    
    def test_client_creation(self, db_session):
        """Test client creation"""
        client = Client(
            name='Test Client',
            organization='Test Org',
            email='client@example.com',
            phone='+1-555-0123',
            address='123 Test St, Test City, TC 12345'
        )
        
        db_session.add(client)
        db_session.commit()
        
        assert client.id is not None
        assert client.name == 'Test Client'
        assert client.organization == 'Test Org'
        assert client.email == 'client@example.com'
        
    def test_client_display_name(self, db_session):
        """Test client display name"""
        client_with_org = Client(name='John Doe', organization='Acme Corp')
        client_without_org = Client(name='Jane Smith')
        
        assert client_with_org.display_name == 'Acme Corp - John Doe'
        assert client_without_org.display_name == 'Jane Smith'
        
    def test_client_to_dict(self, db_session):
        """Test client to dictionary conversion"""
        client = Client(name='Test Client', organization='Test Org')
        
        client_dict = client.to_dict()
        
        assert client_dict['name'] == 'Test Client'
        assert client_dict['organization'] == 'Test Org'
        assert 'contract_count' in client_dict


class TestContractModel:
    """Test Contract model functionality"""
    
    def test_contract_creation(self, db_session):
        """Test contract creation"""
        # Create a user and client first
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db_session.add(user)
        
        client = Client(name='Test Client')
        db_session.add(client)
        
        db_session.commit()
        
        contract = Contract(
            title='Test Contract',
            description='Test contract description',
            client_id=client.id,
            contract_type='Service',
            status=Contract.STATUS_DRAFT,
            contract_value=10000.00,
            created_date=date.today(),
            created_by=user.id
        )
        
        db_session.add(contract)
        db_session.commit()
        
        assert contract.id is not None
        assert contract.title == 'Test Contract'
        assert contract.status == Contract.STATUS_DRAFT
        assert contract.client_id == client.id
        assert contract.created_by == user.id
        
    def test_contract_status_update(self, db_session):
        """Test contract status update"""
        # Create test data
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db_session.add(user)
        
        client = Client(name='Test Client')
        db_session.add(client)
        
        contract = Contract(
            title='Test Contract',
            client_id=client.id,
            contract_type='Service',
            created_by=user.id
        )
        
        db_session.add(contract)
        db_session.commit()
        
        # Update status
        status_history = contract.update_status(
            Contract.STATUS_ACTIVE, 
            user.id, 
            'Contract activated'
        )
        
        db_session.commit()
        
        assert contract.status == Contract.STATUS_ACTIVE
        assert status_history.old_status == Contract.STATUS_DRAFT
        assert status_history.new_status == Contract.STATUS_ACTIVE
        assert status_history.changed_by == user.id
        
    def test_contract_soft_delete(self, db_session):
        """Test contract soft delete"""
        # Create test data
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db_session.add(user)
        
        client = Client(name='Test Client')
        db_session.add(client)
        
        contract = Contract(
            title='Test Contract',
            client_id=client.id,
            contract_type='Service',
            created_by=user.id
        )
        
        db_session.add(contract)
        db_session.commit()
        
        # Soft delete
        contract.soft_delete(user.id)
        db_session.commit()
        
        assert contract.deleted_at is not None
        assert contract.status == Contract.STATUS_DELETED
        
    def test_contract_is_expired(self, db_session):
        """Test contract expiration check"""
        # Create test data
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db_session.add(user)
        
        client = Client(name='Test Client')
        db_session.add(client)
        
        # Contract with past expiration date
        expired_contract = Contract(
            title='Expired Contract',
            client_id=client.id,
            contract_type='Service',
            expiration_date=date.today() - timedelta(days=1),
            created_by=user.id
        )
        
        # Contract with future expiration date
        active_contract = Contract(
            title='Active Contract',
            client_id=client.id,
            contract_type='Service',
            expiration_date=date.today() + timedelta(days=30),
            created_by=user.id
        )
        
        db_session.add_all([expired_contract, active_contract])
        db_session.commit()
        
        assert expired_contract.is_expired() is True
        assert active_contract.is_expired() is False
        
    def test_contract_to_dict(self, db_session):
        """Test contract to dictionary conversion"""
        # Create test data
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db_session.add(user)
        
        client = Client(name='Test Client')
        db_session.add(client)
        
        contract = Contract(
            title='Test Contract',
            client_id=client.id,
            contract_type='Service',
            created_by=user.id
        )
        
        db_session.add(contract)
        db_session.commit()
        
        contract_dict = contract.to_dict()
        
        assert contract_dict['title'] == 'Test Contract'
        assert contract_dict['client_id'] == client.id
        assert contract_dict['status'] == Contract.STATUS_DRAFT
        assert 'is_deleted' in contract_dict


class TestContractStatusHistory:
    """Test ContractStatusHistory model"""
    
    def test_status_history_creation(self, db_session):
        """Test status history creation"""
        history = ContractStatusHistory(
            contract_id=1,
            old_status='draft',
            new_status='active',
            changed_by=1,
            change_reason='Contract approved'
        )
        
        assert history.old_status == 'draft'
        assert history.new_status == 'active'
        assert history.change_reason == 'Contract approved'
        
    def test_status_history_to_dict(self, db_session):
        """Test status history to dictionary conversion"""
        history = ContractStatusHistory(
            contract_id=1,
            old_status='draft',
            new_status='active',
            changed_by=1,
            change_reason='Contract approved'
        )
        
        history_dict = history.to_dict()
        
        assert history_dict['old_status'] == 'draft'
        assert history_dict['new_status'] == 'active'
        assert history_dict['change_reason'] == 'Contract approved'


class TestContractAccessHistory:
    """Test ContractAccessHistory model"""
    
    def test_access_history_creation(self, db_session):
        """Test access history creation"""
        access = ContractAccessHistory(
            contract_id=1,
            accessed_by=1,
            access_type='view',
            ip_address='127.0.0.1',
            user_agent='Test Browser'
        )
        
        assert access.contract_id == 1
        assert access.accessed_by == 1
        assert access.access_type == 'view'
        assert access.ip_address == '127.0.0.1'
        
    def test_access_history_to_dict(self, db_session):
        """Test access history to dictionary conversion"""
        access = ContractAccessHistory(
            contract_id=1,
            accessed_by=1,
            access_type='view',
            ip_address='127.0.0.1'
        )
        
        access_dict = access.to_dict()
        
        assert access_dict['contract_id'] == 1
        assert access_dict['accessed_by'] == 1
        assert access_dict['access_type'] == 'view'
        assert access_dict['ip_address'] == '127.0.0.1'
