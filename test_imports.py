#!/usr/bin/env python3
"""
Test script to verify imports work correctly
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        print("✓ Importing Flask app...")
        from app import create_app, db
        
        print("✓ Importing models...")
        from app.models.user import User
        from app.models.client import Client
        from app.models.contract import Contract
        
        print("✓ Importing services...")
        from app.services.auth_service import AuthService
        from app.services.contract_service import ContractService
        from app.services.file_service import FileService
        
        print("✓ Importing routes...")
        from app.routes.auth import auth_bp
        from app.routes.contracts import contracts_bp
        
        print("✓ Importing utilities...")
        from app.utils.validators import validate_file_extension
        from app.utils.helpers import format_file_size
        
        print("\n🎉 All imports successful! No circular import issues detected.")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
