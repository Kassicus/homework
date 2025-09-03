#!/usr/bin/env python3
"""
Contract and Client Data Import Script
Imports realistic contract data from the planning document into the database
"""
import os
import sys
from datetime import datetime, date
from decimal import Decimal

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.client import Client
from app.models.contract import Contract
from app.models.user import User

def parse_date(date_str):
    """Parse date string in YYYY-MM-DD format"""
    if not date_str or date_str.strip() == '':
        return None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date()
    except ValueError:
        print(f"Warning: Could not parse date '{date_str}'")
        return None

def parse_value(value_str):
    """Parse contract value string (e.g., '$125,000/year' -> 125000)"""
    if not value_str or value_str.strip() == '':
        return None
    
    # Remove common prefixes/suffixes and formatting
    clean_value = value_str.replace('$', '').replace(',', '').replace('/year', '').strip()
    
    try:
        return Decimal(clean_value)
    except:
        print(f"Warning: Could not parse value '{value_str}'")
        return None

def map_status(status_str):
    """Map status strings to database status constants"""
    status_mapping = {
        'Active': Contract.STATUS_ACTIVE,
        'Expiring Soon': Contract.STATUS_ACTIVE,  # Still active but expiring
        'Under Review': Contract.STATUS_UNDER_REVIEW,
        'Draft': Contract.STATUS_DRAFT,
        'Terminated': Contract.STATUS_TERMINATED,
        'Expired': Contract.STATUS_EXPIRED,
        'Completed': Contract.STATUS_TERMINATED,
    }
    return status_mapping.get(status_str, Contract.STATUS_DRAFT)

def get_or_create_client(name, client_type_hint=None):
    """Get existing client or create new one"""
    # Check if client already exists
    existing_client = Client.query.filter_by(name=name).first()
    if existing_client:
        return existing_client
    
    # Determine organization vs individual based on name patterns
    organization = None
    if any(word in name.lower() for word in ['corp', 'inc', 'llc', 'ltd', 'company', 'group', 'services', 'solutions', 'systems', 'center', 'district', 'government', 'county', 'city', 'state', 'university', 'school', 'hospital', 'medical']):
        organization = name
        name = name  # Keep the full name as the client name
    
    # Create new client
    client = Client(
        name=name,
        organization=organization,
        email=f"contact@{name.lower().replace(' ', '').replace(',', '').replace('.', '')}example.com"[:120],  # Generate placeholder email
        phone="555-0100",  # Placeholder phone
        address="123 Business St, City, State 12345"  # Placeholder address
    )
    
    db.session.add(client)
    db.session.flush()  # Get the ID
    return client

def import_contract_data():
    """Import all contract data from the realistic contract list"""
    
    print("Starting contract data import...")
    
    # Get the admin user (assuming user ID 1 is admin)
    admin_user = User.query.filter_by(is_admin=True).first()
    if not admin_user:
        print("Error: No admin user found. Please create an admin user first.")
        return False
    
    # Contract data organized by category
    contracts_data = [
        # Retirement Plan Administration
        {
            'title': '401(k) Plan Administration Agreement',
            'client_name': 'Metro City Public Works',
            'contract_type': 'Retirement Administration',
            'value': '$125,000',
            'effective_date': '2024-01-01',
            'expiration_date': '2026-12-31',
            'status': 'Active',
            'description': 'Comprehensive 401(k) plan administration services including participant enrollment, contribution processing, compliance testing, and reporting.'
        },
        {
            'title': '403(b) Plan Management Services',
            'client_name': 'Riverside School District',
            'contract_type': 'Retirement Administration',
            'value': '$89,500',
            'effective_date': '2023-07-01',
            'expiration_date': '2025-06-30',
            'status': 'Active',
            'description': 'Management of 403(b) retirement plans for educational institution employees including investment oversight and participant services.'
        },
        {
            'title': 'Pension Plan Administration',
            'client_name': 'Johnson County Government',
            'contract_type': 'Retirement Administration',
            'value': '$245,000',
            'effective_date': '2024-03-01',
            'expiration_date': '2027-02-28',
            'status': 'Active',
            'description': 'Full-service pension plan administration for county government employees including benefit calculations and distribution processing.'
        },
        {
            'title': '401(k) Fiduciary Services Agreement',
            'client_name': 'Advanced Manufacturing Corp',
            'contract_type': 'Retirement Administration',
            'value': '$156,000',
            'effective_date': '2023-09-15',
            'expiration_date': '2025-09-14',
            'status': 'Active',
            'description': 'Fiduciary services for 401(k) plan including investment selection, monitoring, and ERISA compliance oversight.'
        },
        {
            'title': 'Deferred Compensation Plan Services',
            'client_name': 'State University Medical Center',
            'contract_type': 'Retirement Administration',
            'value': '$198,000',
            'effective_date': '2024-02-01',
            'expiration_date': '2027-01-31',
            'status': 'Active',
            'description': 'Administration of deferred compensation plans for medical center staff including 457(b) and supplemental retirement programs.'
        },
        {
            'title': 'Multi-Employer Pension Administration',
            'client_name': 'Regional Construction Alliance',
            'contract_type': 'Retirement Administration',
            'value': '$312,000',
            'effective_date': '2023-05-01',
            'expiration_date': '2026-04-30',
            'status': 'Active',
            'description': 'Multi-employer pension plan administration serving construction industry workers across the region.'
        },
        
        # Healthcare Benefits Administration
        {
            'title': 'HSA Administration Services',
            'client_name': 'TechSolutions Inc',
            'contract_type': 'Healthcare Administration',
            'value': '$67,500',
            'effective_date': '2024-01-01',
            'expiration_date': '2024-12-31',
            'status': 'Active',
            'description': 'Health Savings Account administration including account setup, contribution processing, and debit card management.'
        },
        {
            'title': 'FSA Management Agreement',
            'client_name': 'City of Westfield',
            'contract_type': 'Healthcare Administration',
            'value': '$45,000',
            'effective_date': '2023-10-01',
            'expiration_date': '2024-09-30',
            'status': 'Expiring Soon',
            'description': 'Flexible Spending Account management for city employees including claims processing and compliance administration.'
        },
        {
            'title': 'HRA Administration Contract',
            'client_name': 'Regional Healthcare System',
            'contract_type': 'Healthcare Administration',
            'value': '$134,000',
            'effective_date': '2024-04-01',
            'expiration_date': '2026-03-31',
            'status': 'Active',
            'description': 'Health Reimbursement Arrangement administration providing comprehensive claims processing and account management.'
        },
        {
            'title': 'COBRA Administration Services',
            'client_name': 'Downtown Medical Group',
            'contract_type': 'Healthcare Administration',
            'value': '$23,500',
            'effective_date': '2023-11-01',
            'expiration_date': '2024-10-31',
            'status': 'Expiring Soon',
            'description': 'COBRA continuation coverage administration including notification, enrollment, and premium collection services.'
        },
        {
            'title': 'Benefits Enrollment Platform',
            'client_name': 'Midwest Manufacturing LLC',
            'contract_type': 'Healthcare Administration',
            'value': '$78,000',
            'effective_date': '2024-06-01',
            'expiration_date': '2025-05-31',
            'status': 'Active',
            'description': 'Online benefits enrollment platform providing employee self-service capabilities and real-time eligibility management.'
        },
        {
            'title': 'Consumer-Driven Health Plan Admin',
            'client_name': 'Green Valley Township',
            'contract_type': 'Healthcare Administration',
            'value': '$92,000',
            'effective_date': '2023-08-15',
            'expiration_date': '2025-08-14',
            'status': 'Active',
            'description': 'Administration of consumer-driven health plans including HSA coordination and high-deductible plan management.'
        },
        
        # Public Sector Specialized Contracts
        {
            'title': 'Municipal Employee Benefits Program',
            'client_name': 'City of Riverside',
            'contract_type': 'Public Sector Benefits',
            'value': '$456,000',
            'effective_date': '2024-01-01',
            'expiration_date': '2026-12-31',
            'status': 'Active',
            'description': 'Comprehensive employee benefits program for municipal workers including health, dental, vision, and retirement benefits.'
        },
        {
            'title': 'State Retirement System Support',
            'client_name': 'Colorado State Employees',
            'contract_type': 'Public Sector Benefits',
            'value': '$1,250,000',
            'effective_date': '2023-07-01',
            'expiration_date': '2028-06-30',
            'status': 'Active',
            'description': 'Large-scale retirement system support for state employees including PERA administration and benefit counseling.'
        },
        {
            'title': 'Teacher Retirement Plan Services',
            'client_name': 'Northern Valley Education Coop',
            'contract_type': 'Public Sector Benefits',
            'value': '$189,000',
            'effective_date': '2024-08-01',
            'expiration_date': '2027-07-31',
            'status': 'Active',
            'description': 'Specialized retirement plan services for education cooperative covering multiple school districts.'
        },
        {
            'title': 'County Employee Health Benefits',
            'client_name': 'Madison County Government',
            'contract_type': 'Public Sector Benefits',
            'value': '$267,000',
            'effective_date': '2023-12-01',
            'expiration_date': '2025-11-30',
            'status': 'Active',
            'description': 'County employee health benefits administration including medical, dental, and wellness program management.'
        },
        
        # Technology and Platform Contracts
        {
            'title': 'Benefits Administration Software License',
            'client_name': 'BenefitTech Solutions',
            'contract_type': 'Software License',
            'value': '$145,000',
            'effective_date': '2024-01-01',
            'expiration_date': '2026-12-31',
            'status': 'Active',
            'description': 'Enterprise benefits administration software licensing with full technical support and maintenance.'
        },
        {
            'title': 'Payroll Integration Platform',
            'client_name': 'DataSync Systems',
            'contract_type': 'Software Integration',
            'value': '$78,000',
            'effective_date': '2023-06-01',
            'expiration_date': '2025-05-31',
            'status': 'Active',
            'description': 'Payroll system integration platform enabling seamless data exchange between HR and benefits systems.'
        },
        {
            'title': 'Compliance Reporting System',
            'client_name': 'RegTech Compliance',
            'contract_type': 'Software License',
            'value': '$92,000',
            'effective_date': '2024-02-15',
            'expiration_date': '2025-02-14',
            'status': 'Active',
            'description': 'Automated compliance reporting system for ERISA, ACA, and other regulatory requirements.'
        },
        {
            'title': 'Data Backup and Security Services',
            'client_name': 'SecureCloud Technologies',
            'contract_type': 'IT Services',
            'value': '$156,000',
            'effective_date': '2023-09-01',
            'expiration_date': '2026-08-31',
            'status': 'Active',
            'description': 'Comprehensive data backup, disaster recovery, and cybersecurity services for benefits data protection.'
        },
        {
            'title': 'Website Development and Maintenance',
            'client_name': 'WebCraft Digital',
            'contract_type': 'Web Services',
            'value': '$45,000',
            'effective_date': '2024-03-01',
            'expiration_date': '2025-02-28',
            'status': 'Active',
            'description': 'Corporate website development and ongoing maintenance including participant portal integration.'
        },
        {
            'title': 'Mobile App Development Contract',
            'client_name': 'AppBuilders Pro',
            'contract_type': 'Software Development',
            'value': '$125,000',
            'effective_date': '2023-11-01',
            'expiration_date': '2024-04-30',
            'status': 'Under Review',
            'description': 'Custom mobile application development for employee benefits access and account management.'
        },
        
        # Professional Services Contracts
        {
            'title': 'Third-Party Administrator Agreement',
            'client_name': 'Retirement Plan Specialists',
            'contract_type': 'TPA Services',
            'value': '$234,000',
            'effective_date': '2024-01-01',
            'expiration_date': '2026-12-31',
            'status': 'Active',
            'description': 'Third-party administration services for retirement plans including recordkeeping and participant services.'
        },
        {
            'title': 'Actuarial Services Contract',
            'client_name': 'Premier Actuarial Group',
            'contract_type': 'Actuarial Services',
            'value': '$87,000',
            'effective_date': '2023-07-01',
            'expiration_date': '2024-06-30',
            'status': 'Expiring Soon',
            'description': 'Actuarial consulting services for pension plan valuations and compliance testing.'
        },
        {
            'title': 'Investment Advisory Services',
            'client_name': 'Fiduciary Investment Partners',
            'contract_type': 'Investment Advisory',
            'value': '$156,000',
            'effective_date': '2024-04-01',
            'expiration_date': '2027-03-31',
            'status': 'Active',
            'description': 'Investment advisory services for retirement plan assets including fund selection and performance monitoring.'
        },
        {
            'title': 'Audit Services Agreement',
            'client_name': 'Thompson & Associates CPA',
            'contract_type': 'Professional Services',
            'value': '$67,500',
            'effective_date': '2023-12-01',
            'expiration_date': '2024-11-30',
            'status': 'Active',
            'description': 'Annual audit services for employee benefit plans and compliance with ERISA requirements.'
        },
        {
            'title': 'Legal Compliance Consulting',
            'client_name': 'ERISA Law Group',
            'contract_type': 'Legal Services',
            'value': '$125,000',
            'effective_date': '2024-02-01',
            'expiration_date': '2025-01-31',
            'status': 'Active',
            'description': 'Legal compliance consulting for ERISA, HIPAA, and other employee benefits regulations.'
        },
        {
            'title': 'Recordkeeping Services Agreement',
            'client_name': 'National Record Systems',
            'contract_type': 'Recordkeeping',
            'value': '$189,000',
            'effective_date': '2023-10-01',
            'expiration_date': '2026-09-30',
            'status': 'Active',
            'description': 'Comprehensive recordkeeping services for retirement plans including participant communications and reporting.'
        },
        
        # Insurance and Risk Management
        {
            'title': 'Errors & Omissions Insurance Policy',
            'client_name': 'Professional Liability Insurers',
            'contract_type': 'Insurance Policy',
            'value': '$89,000',
            'effective_date': '2024-01-01',
            'expiration_date': '2024-12-31',
            'status': 'Active',
            'description': 'Professional liability insurance coverage for employee benefits administration services.'
        },
        {
            'title': 'Stop-Loss Insurance Coverage',
            'client_name': 'Risk Management Solutions',
            'contract_type': 'Insurance Policy',
            'value': '$145,000',
            'effective_date': '2023-07-01',
            'expiration_date': '2024-06-30',
            'status': 'Expiring Soon',
            'description': 'Stop-loss insurance coverage for self-funded health plans providing catastrophic claim protection.'
        },
        {
            'title': 'Cyber Liability Insurance',
            'client_name': 'CyberSecure Insurance',
            'contract_type': 'Insurance Policy',
            'value': '$67,000',
            'effective_date': '2024-03-01',
            'expiration_date': '2025-02-28',
            'status': 'Active',
            'description': 'Cybersecurity insurance coverage protecting against data breaches and cyber attacks.'
        },
        {
            'title': 'ERISA Bond Coverage',
            'client_name': 'Fidelity Bond Services',
            'contract_type': 'Insurance Policy',
            'value': '$23,500',
            'effective_date': '2023-11-01',
            'expiration_date': '2024-10-31',
            'status': 'Active',
            'description': 'ERISA fidelity bond coverage protecting plan assets from fiduciary breaches.'
        },
        {
            'title': 'General Liability Insurance',
            'client_name': 'Business Insurance Partners',
            'contract_type': 'Insurance Policy',
            'value': '$45,000',
            'effective_date': '2024-01-15',
            'expiration_date': '2025-01-14',
            'status': 'Active',
            'description': 'General business liability insurance coverage for corporate operations and client services.'
        },
        
        # Communication and Education Contracts
        {
            'title': 'Employee Education Materials Development',
            'client_name': 'Benefits Communication Corp',
            'contract_type': 'Marketing Services',
            'value': '$78,000',
            'effective_date': '2024-01-01',
            'expiration_date': '2024-12-31',
            'status': 'Active',
            'description': 'Development of employee education materials for benefits enrollment and retirement planning.'
        },
        {
            'title': 'Multilingual Translation Services',
            'client_name': 'Global Language Solutions',
            'contract_type': 'Translation Services',
            'value': '$34,000',
            'effective_date': '2023-08-01',
            'expiration_date': '2024-07-31',
            'status': 'Active',
            'description': 'Translation services for benefits materials in multiple languages to serve diverse employee populations.'
        },
        {
            'title': 'Benefits Fair Planning Services',
            'client_name': 'Event Management Pros',
            'contract_type': 'Event Planning',
            'value': '$45,000',
            'effective_date': '2024-02-01',
            'expiration_date': '2024-11-30',
            'status': 'Active',
            'description': 'Planning and coordination of employee benefits fairs and enrollment events.'
        },
        {
            'title': 'Video Production for Training Materials',
            'client_name': 'Corporate Video Solutions',
            'contract_type': 'Media Production',
            'value': '$67,000',
            'effective_date': '2023-10-15',
            'expiration_date': '2024-03-15',
            'status': 'Under Review',
            'description': 'Video production services for employee training materials and benefits communication campaigns.'
        },
        {
            'title': 'Annual Report Design and Printing',
            'client_name': 'Design Print Partners',
            'contract_type': 'Marketing Services',
            'value': '$23,500',
            'effective_date': '2024-01-01',
            'expiration_date': '2024-06-30',
            'status': 'Active',
            'description': 'Design and printing services for annual benefits reports and participant communications.'
        },
        
        # Operational Support Contracts
        {
            'title': 'Office Space Lease Agreement',
            'client_name': 'Downtown Business Center',
            'contract_type': 'Real Estate Lease',
            'value': '$234,000',
            'effective_date': '2023-01-01',
            'expiration_date': '2028-12-31',
            'status': 'Active',
            'description': 'Commercial office space lease for corporate headquarters including parking and common area access.'
        },
        {
            'title': 'Telecommunications Services',
            'client_name': 'Business Telecom Solutions',
            'contract_type': 'Telecom Services',
            'value': '$45,000',
            'effective_date': '2024-01-01',
            'expiration_date': '2025-12-31',
            'status': 'Active',
            'description': 'Business telecommunications services including phone systems, internet, and data connectivity.'
        },
        {
            'title': 'Office Equipment Lease',
            'client_name': 'Business Equipment Rental',
            'contract_type': 'Equipment Lease',
            'value': '$67,000',
            'effective_date': '2023-06-01',
            'expiration_date': '2026-05-31',
            'status': 'Active',
            'description': 'Office equipment lease including copiers, printers, and document management systems.'
        },
        {
            'title': 'Janitorial Services Contract',
            'client_name': 'CleanCorp Services',
            'contract_type': 'Facility Services',
            'value': '$34,000',
            'effective_date': '2024-02-01',
            'expiration_date': '2025-01-31',
            'status': 'Active',
            'description': 'Commercial janitorial services for office facilities including daily cleaning and maintenance.'
        },
        {
            'title': 'Security Services Agreement',
            'client_name': 'SecureGuard Protection',
            'contract_type': 'Security Services',
            'value': '$56,000',
            'effective_date': '2023-09-01',
            'expiration_date': '2024-08-31',
            'status': 'Active',
            'description': 'Physical security services including access control systems and after-hours monitoring.'
        },
        
        # Recently Expired/Terminated Contracts
        {
            'title': '401(k) Plan Administration',
            'client_name': 'Heritage Manufacturing',
            'contract_type': 'Retirement Administration',
            'value': '$98,000',
            'effective_date': '2022-01-01',
            'expiration_date': '2023-12-31',
            'status': 'Terminated',
            'description': '401(k) plan administration services for manufacturing company - contract terminated due to company restructuring.'
        },
        {
            'title': 'HSA Administration Services',
            'client_name': 'Valley Medical Associates',
            'contract_type': 'Healthcare Administration',
            'value': '$45,000',
            'effective_date': '2023-01-15',
            'expiration_date': '2024-01-15',
            'status': 'Expired',
            'description': 'Health Savings Account administration services - contract expired and not renewed.'
        },
        {
            'title': 'IT Support Services Contract',
            'client_name': 'TechSupport Solutions',
            'contract_type': 'IT Services',
            'value': '$67,000',
            'effective_date': '2022-12-01',
            'expiration_date': '2023-11-30',
            'status': 'Terminated',
            'description': 'IT support services contract terminated due to service quality issues.'
        },
        {
            'title': 'Marketing Campaign Development',
            'client_name': 'Creative Marketing Group',
            'contract_type': 'Marketing Services',
            'value': '$34,000',
            'effective_date': '2023-11-01',
            'expiration_date': '2024-02-28',
            'status': 'Terminated',
            'description': 'Marketing campaign development project completed successfully.'
        },
        
        # Contracts Under Negotiation/Draft Status
        {
            'title': '403(b) Plan Administration',
            'client_name': 'Mountain View School District',
            'contract_type': 'Retirement Administration',
            'value': '$156,000',
            'effective_date': '2024-07-01',
            'expiration_date': '2027-06-30',
            'status': 'Draft',
            'description': '403(b) retirement plan administration services for school district - contract in draft stage.'
        },
        {
            'title': 'Employee Benefits Consulting',
            'client_name': 'Regional Hospital Network',
            'contract_type': 'Consulting Services',
            'value': '$189,000',
            'effective_date': '2024-08-01',
            'expiration_date': '2027-07-31',
            'status': 'Under Review',
            'description': 'Comprehensive employee benefits consulting services for hospital network - under client review.'
        },
        {
            'title': 'HRIS Integration Services',
            'client_name': 'Unified Systems Inc',
            'contract_type': 'Software Integration',
            'value': '$78,000',
            'effective_date': '2024-06-15',
            'expiration_date': '2025-06-14',
            'status': 'Draft',
            'description': 'Human Resources Information System integration services - contract being finalized.'
        },
        {
            'title': 'Multi-State Compliance Consulting',
            'client_name': 'Interstate Commerce Group',
            'contract_type': 'Compliance Services',
            'value': '$134,000',
            'effective_date': '2024-09-01',
            'expiration_date': '2026-08-31',
            'status': 'Under Review',
            'description': 'Multi-state employee benefits compliance consulting - under legal review.'
        }
    ]
    
    imported_count = 0
    client_count = 0
    
    try:
        for contract_data in contracts_data:
            print(f"Processing: {contract_data['title']}")
            
            # Get or create client
            client = get_or_create_client(contract_data['client_name'])
            if client.id is None:
                client_count += 1
            
            # Create contract
            contract = Contract(
                title=contract_data['title'],
                description=contract_data.get('description', ''),
                client_id=client.id,
                contract_type=contract_data['contract_type'],
                status=map_status(contract_data['status']),
                contract_value=parse_value(contract_data['value']),
                effective_date=parse_date(contract_data['effective_date']),
                expiration_date=parse_date(contract_data['expiration_date']),
                created_by=admin_user.id,
                created_date=date.today()
            )
            
            db.session.add(contract)
            imported_count += 1
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n✅ Import completed successfully!")
        print(f"📊 Imported {imported_count} contracts")
        print(f"👥 Created {client_count} new clients")
        print(f"🎯 All relationships maintained between clients and contracts")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ Import failed: {str(e)}")
        return False

def main():
    """Main function to run the import"""
    print("🚀 National Benefit Services Contract Data Import")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Check if database is ready
        try:
            db.create_all()  # Ensure tables exist
            
            # Run the import
            success = import_contract_data()
            
            if success:
                print("\n🎉 Import process completed successfully!")
                print("\nNext steps:")
                print("1. Check the dashboard for updated statistics")
                print("2. Browse contracts and clients to verify data")
                print("3. Test search and filtering functionality")
                print("4. Review expiring contracts alerts")
            else:
                print("\n💥 Import process failed. Please check the errors above.")
                sys.exit(1)
                
        except Exception as e:
            print(f"\n💥 Database error: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main()
