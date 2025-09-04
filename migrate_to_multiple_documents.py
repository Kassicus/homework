#!/usr/bin/env python3
"""
Migration script to add multiple document support to contracts
This script:
1. Creates the new contract_documents table
2. Migrates existing single documents to the new system
3. Preserves all existing data
"""
import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.contract import Contract
from app.models.contract_document import ContractDocument

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_document_tables():
    """Create the new contract_documents table"""
    try:
        # Create all tables (will only create missing ones)
        db.create_all()
        logger.info("✓ Contract documents table created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating contract documents table: {e}")
        return False


def migrate_existing_documents():
    """Migrate existing single documents to the new multiple document system"""
    try:
        # Get all contracts that have documents but no entries in the new table
        contracts_with_files = Contract.query.filter(
            Contract.file_name.isnot(None),
            Contract.file_path.isnot(None)
        ).all()
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for contract in contracts_with_files:
            try:
                # Check if already migrated
                existing_docs = contract.documents.count()
                if existing_docs > 0:
                    logger.info(f"Contract {contract.id} already has {existing_docs} documents, skipping")
                    skipped_count += 1
                    continue
                
                # Create document record from legacy fields
                document = ContractDocument(
                    contract_id=contract.id,
                    file_path=contract.file_path,
                    file_name=contract.file_name,
                    original_filename=contract.file_name,  # Use file_name as original
                    file_size=contract.file_size or 0,
                    mime_type=contract.mime_type or "application/octet-stream",
                    extracted_text=contract.extracted_text,
                    document_type="contract",
                    description="Migrated from legacy single document system",
                    uploaded_by=contract.created_by,
                    uploaded_at=contract.created_at,
                    is_primary=True  # First document is always primary
                )
                
                db.session.add(document)
                migrated_count += 1
                
                logger.info(f"Migrated document for contract {contract.id}: {contract.file_name}")
                
            except Exception as e:
                logger.error(f"Error migrating contract {contract.id}: {e}")
                error_count += 1
        
        # Commit all migrations
        db.session.commit()
        
        logger.info(f"Migration completed:")
        logger.info(f"  ✓ Migrated: {migrated_count} documents")
        logger.info(f"  - Skipped: {skipped_count} (already migrated)")
        logger.info(f"  ✗ Errors: {error_count}")
        
        return migrated_count, skipped_count, error_count
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during migration: {e}")
        return 0, 0, 1


def verify_migration():
    """Verify that migration was successful"""
    try:
        total_contracts = Contract.query.count()
        contracts_with_legacy_files = Contract.query.filter(
            Contract.file_name.isnot(None)
        ).count()
        contracts_with_new_docs = Contract.query.join(ContractDocument).distinct().count()
        total_documents = ContractDocument.query.count()
        
        logger.info("Migration Verification:")
        logger.info(f"  Total contracts: {total_contracts}")
        logger.info(f"  Contracts with legacy files: {contracts_with_legacy_files}")
        logger.info(f"  Contracts with new documents: {contracts_with_new_docs}")
        logger.info(f"  Total documents in new system: {total_documents}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False


def main():
    """Main migration function"""
    logger.info("Starting migration to multiple document support...")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Step 1: Create new tables
            logger.info("Step 1: Creating contract_documents table...")
            if not create_document_tables():
                logger.error("Failed to create tables. Aborting migration.")
                return False
            
            # Step 2: Migrate existing documents
            logger.info("Step 2: Migrating existing documents...")
            migrated, skipped, errors = migrate_existing_documents()
            
            if errors > 0:
                logger.warning(f"Migration completed with {errors} errors")
            
            # Step 3: Verify migration
            logger.info("Step 3: Verifying migration...")
            if verify_migration():
                logger.info("✓ Migration completed successfully!")
                return True
            else:
                logger.error("Migration verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Migration to multiple document support completed successfully!")
        print("You can now:")
        print("  - Upload multiple documents per contract")
        print("  - Delete individual documents")
        print("  - Set primary documents")
        print("  - Organize documents by type")
    else:
        print("\n❌ Migration failed. Check the logs above for details.")
        sys.exit(1)
