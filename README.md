# Certificate-Based Network Compliance & Access Control System

A comprehensive enterprise-grade network security system that enforces certificate-based authentication for network access control. Only devices possessing valid certificates signed by the organization's private Certificate Authority (CA) can access the network.

## 🚀 Features

### Core Capabilities
- **Private Certificate Authority (CA)**: Generate and manage X.509 certificates for network devices
- **Device Registration**: Register devices with hostname, MAC address, IP, device type, and department
- **FreeRADIUS Integration**: EAP-TLS authentication for wireless and wired network access
- **Compliance Monitoring**: Real-time network scanning and compliance checking
- **Device Fingerprinting**: OS and vendor identification using MAC OUI, TCP/IP, and DHCP fingerprinting
- **Alert System**: Real-time alerts for unauthorized devices, MAC spoofing, hostname changes, and more
- **Modern Dashboard**: React-based dashboard with real-time monitoring and analytics
- **RBAC**: Role-based access control (Admin, User, Auditor)
- **Audit Logging**: Complete audit trail of all authentication attempts and administrative actions

### Security Features
- Certificate-based device authentication
- Certificate revocation and CRL support
- MAC address validation and spoofing detection
- Hostname compliance checking
- Device quarantine capabilities
- VLAN assignment based on device authorization
- Encrypted communication (TLS)
- JWT-based API authentication

## 📋 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                          │
│                    Dashboard & Admin UI                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                              │
│              REST API + WebSocket + Certificate Service           │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
│   PostgreSQL    │ │ FreeRADIUS  │ │  Monitoring  │
│   Database      │ │   Server    │ │   Service    │
└─────────────────┘ └─────────────┘ └──────────────┘
```

## 🛠️ Tech Stack

### Backend
- **Python 3.11+**: Core language
- **Flask**: Web framework
- **SQLAlchemy**: ORM
- **PostgreSQL**: Database
- **cryptography**: Certificate generation and validation
- **scapy**: Network packet analysis
- **psutil**: System monitoring
- **Flask-JWT-Extended**: JWT authentication
- **Flask-SocketIO**: WebSocket support

### Frontend
- **React 18**: UI framework
- **Vite**: Build tool
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Lucide React**: Icons
- **axios**: HTTP client
- **socket.io-client**: WebSocket client

### Infrastructure
- **FreeRADIUS**: Authentication server
- **Docker & Docker Compose**: Containerization
- **Nginx**: Reverse proxy

## 📦 Project Structure

```
network-monitor-project/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routes/          # API endpoints
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utilities
│   │   └── database.py      # Database configuration
│   ├── main.py              # Flask application entry point
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   ├── contexts/        # React contexts
│   │   └── services/        # API services
│   ├── package.json         # Node dependencies
│   └── vite.config.js      # Vite configuration
├── freeradius/
│   ├── config/              # FreeRADIUS configuration
│   └── scripts/             # Certificate validation scripts
├── certificates/
│   ├── ca/                  # CA certificates
│   ├── issued/              # Issued device certificates
│   └── revoked/             # Revoked certificates
├── monitoring/
│   ├── scripts/             # Monitoring scripts
│   └── logs/                # Monitoring logs
├── database/
│   └── init.sql             # Database initialization
├── docker/
│   ├── docker-compose.yml   # Docker Compose configuration
│   ├── Dockerfile.backend   # Backend Dockerfile
│   ├── Dockerfile.frontend  # Frontend Dockerfile
│   └── nginx.conf           # Nginx configuration
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- PostgreSQL 15+ (for local development)

### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd network-monitor-project
```

2. **Configure environment variables**
```bash
cp backend/.env.example backend/.env
```

Edit `.env` with your configuration:
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/network_compliance
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production
DEBUG=True
PORT=5000
NETWORK_RANGE=192.168.1.0/24
POLL_INTERVAL=30
```

3. **Start all services**
```bash
cd docker
docker-compose up -d
```

4. **Access the application**
- Frontend Dashboard: http://localhost:3000
- Backend API: http://localhost:5000
- FreeRADIUS: localhost:1812 (auth), localhost:1813 (acct)

5. **Default credentials**
- Username: `admin`
- Password: `admin123`
- **Important**: Change the default password immediately after first login!

### Local Development Setup

1. **Set up PostgreSQL**
```bash
# Create database
createdb network_compliance

# Run initialization script
psql network_compliance < database/init.sql
```

2. **Install backend dependencies**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Install frontend dependencies**
```bash
cd frontend
npm install
```

4. **Start backend**
```bash
cd backend
python main.py
```

5. **Start frontend**
```bash
cd frontend
npm run dev
```

6. **Start monitoring service**
```bash
cd monitoring
python monitor.py
```

## 📖 Usage Guide

### Device Registration

1. **Register a new device**
```bash
curl -X POST http://localhost:5000/api/devices \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt-token>" \
  -d '{
    "hostname": "IT-WS-0042",
    "mac_address": "00:11:22:33:44:55",
    "ip_address": "192.168.1.10",
    "device_type": "WS",
    "department": "IT"
  }'
```

2. **Generate certificate for device**
```bash
curl -X POST http://localhost:5000/api/certificates/generate/1 \
  -H "Authorization: Bearer <jwt-token>"
```

3. **Download certificate bundle**
```bash
curl -X GET http://localhost:5000/api/certificates/1/download \
  -H "Authorization: Bearer <jwt-token>" \
  --output device_bundle.pem
```

### FreeRADIUS Configuration

1. **Copy CA certificate to FreeRADIUS**
```bash
cd freeradius/scripts
chmod +x setup_certs.sh
./setup_certs.sh
```

2. **Configure network devices** (switches, APs) to use FreeRADIUS for authentication
3. **Enable EAP-TLS** on your network devices
4. **Configure client devices** to use the issued certificates

### Monitoring

The monitoring service automatically:
- Scans the network at configured intervals
- Detects unauthorized devices
- Checks for MAC spoofing
- Validates hostname compliance
- Generates alerts for violations

Start monitoring:
```bash
curl -X POST http://localhost:5000/api/monitoring/start \
  -H "Authorization: Bearer <jwt-token>"
```

## 🔧 Configuration

### Backend Configuration (backend/.env)
```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Network
NETWORK_RANGE=192.168.1.0/24
POLL_INTERVAL=30

# SMTP (for email alerts)
SMTP_HOST=smtp.company.com
SMTP_PORT=587
SMTP_USER=alerts@company.com
SMTP_PASSWORD=your-password
ADMIN_EMAIL=admin@company.com
```

### FreeRADIUS Configuration
Edit `freeradius/config/radiusd.conf` to configure:
- Database connection
- Certificate paths
- Authentication methods
- Client definitions

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new admin
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Devices
- `GET /api/devices` - List all devices
- `POST /api/devices` - Register new device
- `GET /api/devices/:id` - Get device details
- `POST /api/devices/:id/authorize` - Authorize device
- `POST /api/devices/:id/quarantine` - Quarantine device
- `PUT /api/devices/:id/vlan` - Assign VLAN
- `DELETE /api/devices/:id` - Delete device

### Certificates
- `POST /api/certificates/generate/:device_id` - Generate certificate
- `GET /api/certificates/:id/download` - Download certificate
- `POST /api/certificates/:id/revoke` - Revoke certificate
- `GET /api/certificates/device/:device_id` - Get device certificates
- `GET /api/certificates/ca/info` - Get CA information

### Alerts
- `GET /api/alerts` - List alerts
- `POST /api/alerts` - Create alert
- `POST /api/alerts/:id/resolve` - Resolve alert
- `GET /api/alerts/stats` - Get alert statistics

### Monitoring
- `POST /api/monitoring/start` - Start monitoring
- `POST /api/monitoring/stop` - Stop monitoring
- `GET /api/monitoring/status` - Get monitoring status
- `GET /api/monitoring/devices` - Get detected devices
- `POST /api/monitoring/scan` - Trigger manual scan

### Compliance
- `GET /api/compliance/score` - Get compliance score
- `POST /api/compliance/report` - Generate report
- `GET /api/compliance/reports` - List reports
- `GET /api/compliance/reports/:id` - Get report details
- `GET /api/compliance/metrics` - Get real-time metrics

## 🔒 Security Considerations

1. **Change default passwords** immediately
2. **Use strong secrets** for SECRET_KEY and JWT_SECRET_KEY
3. **Enable HTTPS** in production
4. **Restrict network access** to FreeRADIUS server
5. **Regularly rotate certificates** (recommended: annually)
6. **Monitor alerts** for suspicious activity
7. **Implement proper firewall rules**
8. **Use VLANs** to isolate unauthorized devices
9. **Enable audit logging** and review regularly
10. **Backup certificates** and CA private key securely

## 🧪 Testing

### Run backend tests
```bash
cd backend
pytest tests/
```

### Run frontend tests
```bash
cd frontend
npm test
```

### Test certificate generation
```python
from backend.app.services.certificate_service import CertificateService

cert_service = CertificateService()
ca_info = cert_service.get_ca_info()
print(ca_info)
```

## 📈 Monitoring and Logging

### Backend Logs
- Location: `backend/logs/monitor.log`
- Contains: API requests, errors, monitoring events

### Monitoring Logs
- Location: `monitoring/logs/monitor.log`
- Contains: Network scan results, compliance checks

### Database Logs
- PostgreSQL logs available in Docker container

## 🐛 Troubleshooting

### Common Issues

1. **Database connection failed**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Check database credentials

2. **Certificate generation fails**
   - Verify CA certificates exist in `certificates/ca/`
   - Check file permissions
   - Ensure cryptography library is installed

3. **FreeRADIUS authentication fails**
   - Verify certificate paths in FreeRADIUS config
   - Check database connection
   - Review FreeRADIUS logs

4. **Monitoring not detecting devices**
   - Check NETWORK_RANGE configuration
   - Verify Scapy is installed
   - Check network permissions
   - Ensure proper network interface

5. **Frontend cannot connect to backend**
   - Check CORS configuration
   - Verify backend is running
   - Check proxy configuration in nginx.conf

## 📚 Additional Resources

- [FreeRADIUS Documentation](https://wiki.freeradius.org/)
- [Python cryptography library](https://cryptography.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)
- [Scapy Documentation](https://scapy.readthedocs.io/)

## 🤝 Contributing

This is an enterprise security project. For contributions:
1. Follow security best practices
2. Add tests for new features
3. Update documentation
4. Ensure code passes linting

## 📄 License

This project is for educational and enterprise demonstration purposes.

## 👥 Support

For issues and questions:
- Check the troubleshooting section
- Review logs in `logs/` directories
- Consult the API documentation

## 🎯 Use Cases

- **Enterprise Network Access Control**: Enforce certificate-based authentication
- **BYOD Security**: Validate and authorize personal devices
- **IoT Device Management**: Secure IoT device onboarding
- **Compliance Monitoring**: Ensure network policy compliance
- **Security Auditing**: Track all network access attempts
- **Incident Response**: Quickly identify and quarantine unauthorized devices

---

**Built for enterprise network security and cybersecurity education.**
