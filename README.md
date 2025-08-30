# Internal Contract Management Platform

A centralized internal tool for managing contracts with external companies. This platform automates manual workflows, stores contract documents, tracks metadata, and manages the complete contract lifecycle. The platform provides search capabilities, data validation, and a modern web interface for internal use only.

## Features

### Core Functionality
- **Document Management**: Upload and store contracts in PDF, DOCX, DOC, TXT, and RTF formats
- **Text Extraction**: Automatic text extraction from uploaded documents for search indexing
- **Metadata Management**: Comprehensive contract metadata including client info, dates, values, and status
- **Search & Filtering**: Full-text search across contract content and metadata with advanced filtering
- **Lifecycle Management**: Complete contract lifecycle from draft to expiration with status tracking
- **Audit Trail**: Comprehensive logging of all status changes and document access

### User Management
- **Authentication**: Secure internal user login system
- **Role-Based Access**: Admin and standard user roles with appropriate permissions
- **User Profiles**: User management and password change functionality

### Dashboard & Reporting
- **Overview Dashboard**: Contract statistics, recent activity, and quick actions
- **Analytics**: Contract value analysis, status distribution, and expiration tracking
- **Reports**: Customizable reports for contracts, clients, and user activity

### Security & Compliance
- **Soft Delete**: 30-day retention of deleted contracts before permanent removal
- **Access Logging**: Complete audit trail of document access and modifications
- **Input Validation**: Comprehensive validation of all user inputs and file uploads

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: Flask-Login with bcrypt password hashing
- **File Processing**: PyPDF2, python-docx, built-in Python libraries
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Deployment**: nginx + Gunicorn with .deb packaging

## System Requirements

- **Python**: 3.8 or higher
- **Memory**: Minimum 2GB RAM
- **Storage**: 125GB+ for document storage
- **OS**: Linux (Ubuntu 18.04+ recommended)

## Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd contract-manager
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
cp env.example .env
# Edit .env with your configuration
```

### 5. Initialize Database
```bash
python init_db.py
```

### 6. Run Development Server
```bash
python run.py
```

### 7. Access Application
Open your browser and navigate to `http://localhost:5000`

**Default Admin Credentials**: `admin` / `admin123`

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_APP` | Flask application entry point | `wsgi:app` |
| `FLASK_ENV` | Environment (development/production) | `development` |
| `SECRET_KEY` | Flask secret key for sessions | Auto-generated |
| `DATABASE_URL` | Database connection string | `sqlite:///contracts.db` |
| `UPLOAD_FOLDER` | File upload directory | `uploads` |
| `MAX_UPLOAD_SIZE` | Maximum file size in bytes | `131072000` (125MB) |
| `LOG_LEVEL` | Application log level | `INFO` |

### File Upload Configuration

- **Supported Formats**: PDF, DOCX, DOC, TXT, RTF
- **Text Extraction**: 
  - PDF: PyPDF2 library
  - DOCX/DOC: python-docx library  
  - TXT: Built-in Python text processing
  - RTF: Regex-based RTF markup removal
- **Maximum Size**: 125MB per file
- **Storage Structure**: Organized by year/month for efficient management
- **Duplicate Handling**: Automatic timestamp-based filename disambiguation

## Database Schema

### Core Tables
- **users**: User accounts and authentication
- **clients**: Client information and contact details
- **contracts**: Main contract data and metadata
- **contract_status_history**: Audit trail of status changes
- **contract_access_history**: Document access logging

### Key Features
- **Soft Delete**: Contracts marked as deleted but retained for 30 days
- **Audit Trail**: Complete history of all modifications and access
- **Relationships**: Proper foreign key constraints and cascading operations

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/register` - User registration
- `GET /auth/profile` - User profile

### Contracts
- `GET /contracts/` - List all contracts
- `GET /contracts/search` - Search contracts
- `POST /contracts/new` - Create new contract
- `GET /contracts/<id>` - View contract details
- `PUT /contracts/<id>/edit` - Edit contract
- `DELETE /contracts/<id>/delete` - Soft delete contract

### Clients
- `GET /clients/` - List all clients
- `POST /clients/new` - Create new client
- `GET /clients/<id>` - View client details
- `PUT /clients/<id>/edit` - Edit client

### Dashboard
- `GET /dashboard/` - Main dashboard
- `GET /dashboard/contracts` - Contracts overview
- `GET /dashboard/reports` - Reports and analytics
- `GET /dashboard/activity` - Activity feed

## Development

### Project Structure
```
contract-manager/
├── app/                    # Application package
│   ├── __init__.py        # Flask app factory
│   ├── config.py          # Configuration classes
│   ├── models/            # Database models
│   ├── routes/            # Route blueprints
│   ├── services/          # Business logic services
│   └── utils/             # Utility functions
├── templates/              # Jinja2 templates
├── static/                 # Static files (CSS, JS, images)
├── uploads/                # File upload directory
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
├── init_db.py             # Database initialization
├── run.py                 # Development server
└── wsgi.py                # Production WSGI entry point
```

### Code Quality
- **Linting**: flake8 for code style enforcement
- **Formatting**: black for consistent code formatting
- **Import Sorting**: isort for organized imports
- **Testing**: pytest for unit and integration tests

### Development Commands
```bash
# Code formatting
black app/
isort app/

# Linting
flake8 app/

# Testing
pytest

# Database reset
python init_db.py --reset
```

## Deployment

### Production Setup
1. **Server Requirements**: Ubuntu 18.04+ with Python 3.8+
2. **Web Server**: nginx as reverse proxy
3. **WSGI Server**: Gunicorn for Flask application
4. **Process Management**: systemd for service management

### .deb Package Installation
```bash
# Install package
sudo dpkg -i contract-manager_1.0.0.deb

# Configure services
sudo systemctl enable contract-manager
sudo systemctl start contract-manager

# Verify installation
sudo systemctl status contract-manager
```

### Manual Deployment
```bash
# Clone and setup
git clone <repository-url>
cd contract-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configuration
cp env.example .env
# Edit .env for production settings

# Database setup
python init_db.py

# Run with Gunicorn
gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
```

## Monitoring & Logging

### Log Files
- **Application Logs**: `/var/log/contract-manager/contract-manager.log`
- **Access Logs**: nginx access logs
- **Error Logs**: nginx error logs

### Health Checks
- **Endpoint**: `/health`
- **Response**: JSON status and service information
- **Monitoring**: Use for load balancer health checks

## Backup & Recovery

### Automated Backups
- **Daily Backups**: Database and uploaded files
- **Retention**: 30 daily backups, 12 monthly backups
- **Location**: `/var/backups/contract-manager/`

### Manual Backup
```bash
# Database backup
sqlite3 contracts.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# File backup
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
```

## Security Considerations

### Authentication
- **Password Hashing**: bcrypt with salt
- **Session Management**: Secure session cookies
- **CSRF Protection**: Flask-WTF CSRF tokens

### File Security
- **Upload Validation**: File type and size restrictions
- **Path Traversal**: Secure filename handling
- **Access Control**: User-based file access permissions

### Data Protection
- **Input Sanitization**: XSS prevention
- **SQL Injection**: Parameterized queries via SQLAlchemy
- **Access Logging**: Complete audit trail

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database file permissions
ls -la contracts.db

# Verify database integrity
sqlite3 contracts.db "PRAGMA integrity_check;"
```

#### File Upload Issues
```bash
# Check upload directory permissions
ls -la uploads/

# Verify disk space
df -h uploads/
```

#### Service Startup Issues
```bash
# Check service status
sudo systemctl status contract-manager

# View service logs
sudo journalctl -u contract-manager -f
```

### Performance Optimization
- **Database Indexing**: Ensure proper indexes on frequently queried fields
- **File Storage**: Consider SSD storage for better I/O performance
- **Caching**: Implement Redis caching for frequently accessed data

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and commit: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Create a Pull Request

### Code Standards
- Follow PEP 8 style guidelines
- Write comprehensive docstrings
- Include unit tests for new features
- Update documentation as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

### Documentation
- **API Reference**: See inline code documentation
- **User Guide**: Check the `/help` endpoint in the application
- **Developer Guide**: This README and inline code comments

### Issues & Questions
- **Bug Reports**: Use GitHub Issues
- **Feature Requests**: Submit via GitHub Issues
- **Questions**: Check documentation or submit GitHub Issues

## Roadmap

### Phase 2 Features (Future)
- **OCR Integration**: Text extraction from scanned documents
- **Email Notifications**: Status change and expiration alerts
- **Digital Signatures**: Electronic document signing
- **Advanced Workflows**: Custom approval processes
- **API Development**: RESTful API for external integrations
- **Mobile Application**: iOS/Android apps

### Current Status
- **Phase 1**: ✅ Core Backend (Complete)
- **Phase 2**: 🔄 Frontend Foundation (In Progress)
- **Phase 3**: ⏳ Advanced Features (Planned)
- **Phase 4**: ⏳ Testing & Deployment (Planned)

---

**Internal Contract Management Platform** - Streamlining internal contract workflows since 2025
