# Contract Management Platform - Project Plan

## Project Overview

A centralized contract management platform to automate manual workflows, store contract documents, track metadata, and manage the complete contract lifecycle. The platform will provide search capabilities, data validation, and a modern web interface.

## Technology Stack

- **Backend**: Python Flask
- **Web Server**: nginx (reverse proxy)
- **WSGI Server**: Gunicorn
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **File Storage**: Local filesystem with database references
- **CI/CD**: GitHub Actions
- **Distribution**: .deb package for Ubuntu server deployment
- **Authentication**: Local session-based authentication with user registration
- **Logging**: Python logging module with file rotation

## System Requirements & Constraints

### Scale Expectations
- **Maximum Documents**: 1,000 contracts
- **Concurrent Users**: Up to 10 users
- **Supported File Types**: PDF, DOCX, DOC, TXT, RTF
- **File Size Limit**: 125MB per document
- **Storage Estimate**: ~125GB maximum total storage requirement

### Authentication Model
- **Local Authentication**: Username/password with session management
- **User Registration**: Open registration with admin approval option
- **User Roles**: Standard users and administrators
- **Session Management**: Flask-Login with secure session cookies

### Data Retention Policy
- **Soft Delete**: Deleted contracts retained for 30 days
- **Permanent Deletion**: Automatic cleanup after 30 days
- **Audit Trail**: Permanent retention of status and access history

### 1. Contract Storage & Organization
- Upload contracts in supported formats (PDF, DOCX, DOC, TXT, RTF)
- Store files securely with unique identifiers
- Organize by folders/categories
- Version control for contract updates
- File size and type validation
- Text extraction from documents for search indexing
- Soft delete with 30-day retention before permanent removal

### 2. Metadata Management
- **Client Information**: Name, contact details, organization
- **Contract Details**: Title, description, contract type, value
- **Dates**: Creation, effective, expiration, renewal dates
- **Status Tracking**: Draft, under review, active, expired, terminated, renewed
- **Custom Fields**: Configurable metadata fields
- **Audit Trail**: Status changes and document access history

### 3. Search & Filtering
- Full-text search across contract content and metadata
- Text extraction from PDF and Word documents
- Advanced filtering by:
  - Date ranges
  - Contract status
  - Client name
  - Contract type
  - Custom metadata fields
- Sorting capabilities
- Export search results

### 4. Contract Lifecycle Management
- **Draft**: Initial contract creation
- **Under Review**: Pending approval/modifications
- **Active**: Signed and in effect
- **Expired**: Past expiration date
- **Terminated**: Ended before expiration
- **Renewed**: Extended or updated
- **Deleted**: Soft-deleted, retained for 30 days
- Automated status transitions based on dates
- Complete audit trail for all status changes and document access

## Technical Architecture

### Backend Structure
```
contract_manager/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Flask configuration
│   ├── models/
│   │   ├── __init__.py
│   │   ├── contract.py
│   │   ├── client.py
│   │   └── user.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication blueprints
│   │   ├── contracts.py     # Contract management routes
│   │   ├── clients.py       # Client management routes
│   │   └── dashboard.py     # Dashboard routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── contract_service.py
│   │   ├── file_service.py
│   │   └── notification_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── helpers.py
│   │   └── decorators.py
│   └── static/
│       ├── css/
│       ├── js/
│       └── uploads/
├── templates/
├── requirements.txt
├── wsgi.py                  # Gunicorn WSGI entry point
├── run.py                   # Development server
├── nginx.conf               # nginx configuration template
└── tests/
```

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Clients Table
```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    organization VARCHAR(200),
    email VARCHAR(120),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Contracts Table
```sql
CREATE TABLE contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    client_id INTEGER NOT NULL,
    contract_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'draft',
    contract_value DECIMAL(15,2),
    file_path VARCHAR(500),
    file_name VARCHAR(300),
    file_size INTEGER,
    mime_type VARCHAR(100),
    extracted_text TEXT,
    created_date DATE NOT NULL,
    effective_date DATE,
    expiration_date DATE,
    renewal_date DATE,
    deleted_at TIMESTAMP NULL,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients (id),
    FOREIGN KEY (created_by) REFERENCES users (id)
);
```

#### Contract Status History Table
```sql
CREATE TABLE contract_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by INTEGER NOT NULL,
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts (id),
    FOREIGN KEY (changed_by) REFERENCES users (id)
);
```

#### Contract Access History Table
```sql
CREATE TABLE contract_access_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id INTEGER NOT NULL,
    accessed_by INTEGER NOT NULL,
    access_type VARCHAR(50) NOT NULL, -- 'view', 'download', 'edit'
    ip_address VARCHAR(45),
    user_agent TEXT,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts (id),
    FOREIGN KEY (accessed_by) REFERENCES users (id)
);
```

## Feature Specifications

### 1. File Upload System
- Drag-and-drop interface
- Progress indicators
- File validation (type, size up to 125MB)
- Automatic text extraction from documents
- Document preview generation
- Duplicate file handling with date-based naming

### 2. User Management
- User registration with email verification
- Admin user approval workflow (optional)
- Password reset functionality
- User profile management
- Admin panel for user management

### 3. Dashboard
- Contract statistics overview
- Upcoming expirations alerts
- Recent activity feed
- Quick actions panel
- Status distribution charts
- Personal activity summary

### 4. Contract Management
- CRUD operations for contracts
- Bulk operations (status updates, exports)
- Contract comparison tools
- Template management
- Soft delete with restoration capability
- Document access tracking

### 5. Search System
- Real-time search suggestions
- Full-text search in document content
- Advanced search builder
- Saved searches
- Search history
- Text extraction from PDF/Word documents

### 6. Audit & Reporting
- Contract summary reports
- Expiration reports
- Client activity reports
- Status transition reports
- Document access reports
- User activity reports
- Export to PDF/CSV

### 7. Text Processing
- Automatic text extraction from uploaded documents
- Search indexing of extracted content
- Support for PDF text extraction
- Microsoft Word document processing
- **Future Enhancement**: OCR for scanned documents

## Technical Implementation Details

### File Storage Strategy
```
/var/lib/contract-manager/uploads/
├── 2025/
│   ├── 01/
│   │   ├── contract_report_2025-01-15_143022.pdf
│   │   ├── contract_report_2025-01-15_150134.pdf  # duplicate filename
│   │   └── agreement_draft_2025-01-16_091245.docx
│   └── 02/
└── deleted/
    └── 2025-01-15_contract_report_2025-01-15_143022.pdf
```

### File Naming Convention
- Format: `{original_filename}_{YYYY-MM-DD}_{HHMMSS}.{extension}`
- Duplicate handling: Append upload timestamp to ensure uniqueness
- Deleted files: Prefix with deletion date for 30-day retention

### User Registration Workflow
- **pending**: Registered but awaiting admin approval
- **active**: Approved and can log in
- **inactive**: Suspended by admin
- **rejected**: Registration denied by admin
- **First admin**: Created during package installation process

### Text Extraction Strategy
- **Primary**: PyPDF2 for PDFs, python-docx for Word documents
- **Fallback**: textract library for unsupported formats
- **Error Handling**: Store extraction errors, allow manual text entry
- **Search Implementation**: SQLite FTS4 for full-text search indexing

### Duplicate File Handling
- Allow duplicate files with different metadata
- Automatic filename disambiguation using upload timestamp
- No content-based deduplication (business requirement driven)
- Original filename preserved in database metadata

### Development Data Seeding
- **Default Admin**: `admin/admin123` (development only)
- **Sample Contracts**: 5-10 contracts with various statuses
- **Sample Clients**: 3-5 test client records
- **Sample Text**: Pre-extracted text for search functionality testing

## Data Validation & Security

### Input Validation
- File type restrictions (PDF, DOCX, DOC, TXT, RTF only)
- File size limits (125MB maximum)
- Metadata field validation
- SQL injection prevention
- XSS protection

### Security Measures
- Password hashing (bcrypt)
- Session management
- CSRF protection
- File upload security
- Input sanitization
- Rate limiting

### Error Handling
- Graceful error pages
- Comprehensive logging
- User-friendly error messages
- Exception tracking
- Recovery mechanisms

## User Interface Design

### Design Principles
- Clean, modern interface
- Responsive design
- Accessibility compliance (WCAG 2.1)
- Intuitive navigation
- Consistent styling

### Key Pages
1. **Registration/Login** - User account creation and authentication
2. **Dashboard** - Overview and quick actions
3. **Contracts List** - Searchable/filterable table with soft-deleted items view
4. **Contract Details** - Full contract information with access logging
5. **Add/Edit Contract** - Form-based input with file upload
6. **Client Management** - Client CRUD operations
7. **Reports** - Various reporting views including audit reports
8. **User Management** - Admin panel for user administration
9. **Settings** - System configuration and user preferences

### UI Components
- Navigation sidebar
- Breadcrumb navigation
- Modal dialogs
- Data tables with sorting/filtering
- Form validation feedback
- Progress indicators
- Notification system

## Development Environment Setup

### Prerequisites
- Python 3.8+ installed
- Git for version control
- Text editor/IDE (VS Code recommended)

### Local Development Setup
1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd contract-manager
   ```

2. **Create Python Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with development settings
   ```

5. **Database Setup**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run Development Server**
   ```bash
   python run.py
   ```

### Development Dependencies
```txt
# Core Flask dependencies
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Flask-WTF==1.1.1
Flask-Migrate==4.0.5

# Document processing
PyPDF2==3.0.1
python-docx==0.8.11
textract==1.6.5

# Development tools
pytest==7.4.2
pytest-cov==4.1.0
black==23.9.1
flake8==6.1.0
isort==5.12.0
```

### Phase 1: Core Backend (Weeks 1-2)
- [ ] Flask project setup with application factory pattern
- [ ] Database models and SQLAlchemy integration
- [ ] User registration and authentication system
- [ ] Basic CRUD operations and API endpoints
- [ ] File upload functionality with validation
- [ ] Text extraction service (PDF/Word documents)
- [ ] nginx and Gunicorn configuration templates

### Phase 2: Frontend Foundation (Weeks 3-4)
- [ ] Jinja2 templates and base styling
- [ ] User registration and authentication UI
- [ ] Contract management interface
- [ ] AJAX-powered search with full-text capability
- [ ] Responsive design with CSS Grid/Flexbox
- [ ] Flask-WTF forms integration

### Phase 3: Advanced Features (Weeks 5-6)
- [ ] Advanced search and filtering with extracted text
- [ ] Contract lifecycle management with audit trails
- [ ] Soft delete functionality with 30-day retention
- [ ] Dashboard with analytics and activity feeds
- [ ] Reporting system with audit reports
- [ ] Document access tracking and history

### Phase 4: Testing, Deployment & Backup System (Weeks 7-8)
- [ ] Comprehensive testing suite
- [ ] CI/CD pipeline setup with backup integration
- [ ] Automated backup and restore system
- [ ] .deb package creation with backup hooks
- [ ] Documentation completion
- [ ] Performance optimization

## Testing Strategy

### Unit Tests
- Model validation tests
- Service layer tests
- Utility function tests
- Authentication tests

### Integration Tests
- API endpoint tests
- Database integration tests
- File upload tests
- Search functionality tests

### End-to-End Tests
- User workflow tests
- Browser automation tests
- Performance tests
- Security tests

## Git Branching Strategy

### Branch Structure
- **main**: Production-ready code with feature tags
- **dev**: Integration branch for ongoing development
- **feature/****: Individual feature branches created from dev

### Workflow
1. Create feature branch from `dev`
2. Develop and commit changes
3. Create pull request to merge feature branch into `dev`
4. Automated testing runs on PR to `dev`
5. After PR approval and merge, delete feature branch
6. When major updates are complete, merge `dev` to `main` with feature tag
7. Release package built automatically on tagged commits to `main`

## CI/CD Pipeline

### GitHub Actions Workflows

#### Testing Workflow (`.github/workflows/test.yml`)
**Triggers**: Pull requests to `dev` branch
```yaml
name: Test Suite
on:
  pull_request:
    branches: [dev]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - Code quality checks (flake8, black, isort)
      - Security scanning (bandit, safety)
      - Unit tests with coverage
      - Integration tests
      - Flask app startup test
      - Database migration test
```

#### Release Workflow (`.github/workflows/release.yml`)
**Triggers**: Tags pushed to `main` branch (pattern: `v*.*.*`)
```yaml
name: Build and Release
on:
  push:
    tags:
      - 'v*.*.*'
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - Run full test suite
      - Build .deb package
      - Create GitHub release
      - Upload package artifacts
      - Generate release notes
```

### Deployment Strategy
- **Development**: Automated testing on pull requests to `dev`
- **Staging**: Manual testing environment (optional)
- **Production**: Release packages created on feature tags
- Database migration handling in package postinst scripts
- Rollback via previous package versions

## .deb Package Specifications

### Package Contents
- Flask application files
- nginx configuration template
- Gunicorn systemd service file
- Application systemd service file
- Configuration templates
- Database initialization scripts
- Static files and templates
- Documentation and man pages

### Installation Process
1. Install package dependencies (python3, nginx, python3-pip)
2. Create application user (`contract-manager`)
3. **Backup existing installation** (if upgrading)
4. Setup directory structure:
   - `/opt/contract-manager/` (application files)
   - `/var/lib/contract-manager/` (database and uploads)
   - `/var/log/contract-manager/` (logs)
   - `/etc/contract-manager/` (configuration)
   - `/var/backups/contract-manager/` (automated backups)
5. Initialize SQLite database with schema
6. Configure nginx virtual host
7. Setup Gunicorn systemd service
8. Enable and start services
9. Create initial admin user
10. **Verify installation** and restore backup on failure

### Backup and Restore System
- **Pre-update Backup**: Automatic backup before any system updates
- **Daily Backups**: Automated daily backups of database and uploaded files
- **Backup Retention**: Keep 30 daily backups, 12 monthly backups
- **Automatic Restore**: Restore previous backup if update fails
- **Manual Restore**: Command-line tools for manual backup/restore operations

### Update Process
1. Create timestamped backup of current system
2. Stop application services
3. Install new package version
4. Run database migrations
5. Update configuration files
6. Restart services
7. Verify system health
8. **If failure detected**: Automatic rollback to backup
9. **If success**: Log successful update

### System Services
- `contract-manager.service` (Gunicorn Flask app)
- nginx virtual host configuration
- Log rotation configuration

## Monitoring & Logging

### Logging Strategy
- Application logs (INFO, WARNING, ERROR)
- Access logs
- Security event logs
- Performance metrics
- Error tracking

### Monitoring Points
- Application health
- Database performance
- File system usage
- User activity
- System resources

## Configuration Management

### Environment Variables
```
FLASK_APP=wsgi:app
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:////var/lib/contract-manager/contracts.db
UPLOAD_FOLDER=/var/lib/contract-manager/uploads
MAX_UPLOAD_SIZE=125MB
LOG_LEVEL=INFO
NGINX_SERVER_NAME=your-domain.com
GUNICORN_WORKERS=3
GUNICORN_BIND=127.0.0.1:5000
```

### Configuration Files
- Flask application settings (`/etc/contract-manager/config.py`)
- nginx virtual host (`/etc/nginx/sites-available/contract-manager`)
- Gunicorn configuration (`/etc/contract-manager/gunicorn.conf.py`)
- Logging configuration (`/etc/contract-manager/logging.conf`)
- Email notification settings

## Security Considerations

### Data Protection
- Encrypted file storage (future enhancement)
- Regular backups
- Access control lists
- Audit trails
- GDPR compliance features

### System Security
- Regular security updates
- Vulnerability scanning
- Secure defaults
- Input validation
- Output encoding

## Future Enhancements (Not Currently Planned)

### Potential Phase 2 Features
- **OCR Integration**: Text extraction from scanned documents
- **Email Notifications**: Status change and expiration alerts
- **Digital Signature Integration**: Electronic document signing
- **Advanced Workflow Automation**: Custom approval processes
- **Integration with External Systems**: CRM, accounting software
- **Mobile Application**: iOS/Android apps
- **Advanced Analytics**: Detailed reporting and dashboards
- **Multi-tenant Support**: Organization isolation

### Deferred Features
- **Calendar Integration**: Contract date synchronization
- **Third-party Document Services**: External document processing
- **Advanced User Roles**: Granular permission system
- **API Development**: RESTful API for integrations
- **File Encryption**: At-rest encryption for sensitive documents
- **Advanced Search**: Machine learning-powered search improvements

## Success Metrics

### Performance Targets
- Page load time < 2 seconds
- File upload success rate > 99% (including 125MB files)
- Search response time < 500ms (for up to 1,000 documents)
- Text extraction completion < 60 seconds per document (accommodating larger files)
- System uptime > 99.5%
- Support for 10 concurrent users without performance degradation

### User Experience Goals
- Intuitive navigation requiring minimal training
- Reduced manual workflow time by 70%
- Complete audit trail for compliance requirements
- User satisfaction rating > 4.5/5
- New user onboarding time < 1 hour

## Project Timeline

**Total Estimated Duration: 8 weeks**

- **Week 1-2**: Backend development and database setup
- **Week 3-4**: Frontend development and basic UI
- **Week 5-6**: Advanced features and integrations
- **Week 7**: Testing and bug fixes
- **Week 8**: Documentation, packaging, and deployment

## Risk Assessment

### Technical Risks
- File storage scalability
- Search performance with large datasets
- Database concurrency issues

### Mitigation Strategies
- Implement file size limits
- Database indexing optimization
- Connection pooling
- Regular performance monitoring

## Conclusion

This project plan provides a comprehensive roadmap for developing a robust contract management platform. The modular architecture and phased approach ensure steady progress while maintaining code quality and system reliability. Regular reviews and adjustments to this plan will be necessary as development progresses and requirements evolve.