# Certificate-Based Network Compliance & Access Control System

A comprehensive enterprise-grade network security system that enforces certificate-based authentication for network access control. Only devices possessing valid certificates signed by the organization's private Certificate Authority (CA) can access the network.

## 🚀 Features

### Core Capabilities

* **Private Certificate Authority (CA)**: Generate and manage X.509 certificates for network devices
* **Device Registration**: Register devices with hostname, MAC address, IP, device type, and department
* **FreeRADIUS Integration**: EAP-TLS authentication for wireless and wired network access
* **Compliance Monitoring**: Real-time network scanning and compliance checking
* **Device Fingerprinting**: OS and vendor identification using MAC OUI, TCP/IP, and DHCP fingerprinting
* **Alert System**: Real-time alerts for unauthorized devices, MAC spoofing, hostname changes, and more
* **Modern Dashboard**: React-based dashboard with real-time monitoring and analytics
* **RBAC**: Role-based access control (Admin, User, Auditor)
* **Audit Logging**: Complete audit trail of all authentication attempts and administrative actions

### Security Features

* Certificate-based device authentication
* Certificate revocation and CRL support
* MAC address validation and spoofing detection
* Hostname compliance checking
* Device quarantine capabilities
* VLAN assignment based on device authorization
* Encrypted communication (TLS)
* JWT-based API authentication

## 📋 Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                       │
│                    Dashboard & Admin UI                        │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS / WebSocket
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                           │
│              REST API + WebSocket + Certificate Service        │
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

* **Python 3.11+**: Core language
* **Flask**: Web framework
* **SQLAlchemy**: ORM
* **PostgreSQL**: Database
* **cryptography**: Certificate generation and validation
* **scapy**: Network packet analysis
* **psutil**: System monitoring
* **Flask-JWT-Extended**: JWT authentication
* **Flask-SocketIO**: WebSocket support

### Frontend

* **React 18**: UI framework
* **Vite**: Build tool
* **Tailwind CSS**: Styling
* **Recharts**: Data visualization
* **Lucide React**: Icons
* **axios**: HTTP client
* **socket.io-client**: WebSocket client

### Infrastructure

* **FreeRADIUS**: Authentication server
* **Docker & Docker Compose**: Containerization
* **Nginx**: Reverse proxy

## 📦 Project Structure

```text
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
│   └── vite.config.js       # Vite configuration
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

* Docker and Docker Compose
* Python 3.11+ (for local development)
* Node.js 18+ (for local development)
* PostgreSQL 15+ (for local development)

### Using Docker (Recommended)

1. **Clone the repository**

```bash
git clone <repository-url>
cd network-monitor-project
```

2. **Configure environment variables**
   Create a `.env` file in the repository root.

3. **Start all services**

```bash
docker compose --env-file .env -f docker/docker-compose.yml up -d
```

4. **Access the application**

* Frontend Dashboard: [http://localhost:3000](http://localhost:3000)
* Backend API: [http://localhost:5000](http://localhost:5000)
* FreeRADIUS: localhost:1812 (auth), localhost:1813 (acct)

5. **Create admin account**
   Register the first user via `POST /api/auth/register` or the Sign Up page.

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

## 🔧 Configuration

Example `.env` values:

```env
DATABASE_URL=
SECRET_KEY=
JWT_SECRET_KEY=
NETWORK_RANGE=
POSTGRES_DB=network_compliance
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
VITE_DEV_API_PROXY=http://127.0.0.1:5000
BACKEND_URL=http://localhost:5000
```

## 📊 API Endpoints

### Authentication

* `POST /api/auth/register` - Register new admin
* `POST /api/auth/login` - Login and get JWT token
* `GET /api/auth/me` - Get current user info

### Devices

* `GET /api/devices` - List all devices
* `POST /api/devices` - Register new device
* `GET /api/devices/:id` - Get device details
* `POST /api/devices/:id/authorize` - Authorize device
* `POST /api/devices/:id/quarantine` - Quarantine device
* `PUT /api/devices/:id/vlan` - Assign VLAN
* `DELETE /api/devices/:id` - Delete device

### Certificates

* `POST /api/certificates/generate/:device_id` - Generate certificate
* `GET /api/certificates/:id/download` - Download certificate
* `POST /api/certificates/:id/revoke` - Revoke certificate

### Monitoring

* `POST /api/monitoring/start` - Start monitoring
* `POST /api/monitoring/stop` - Stop monitoring
* `GET /api/monitoring/status` - Get monitoring status

## 🔒 Security Considerations

1. Change default passwords immediately
2. Use strong secrets for SECRET_KEY and JWT_SECRET_KEY
3. Enable HTTPS in production
4. Restrict network access to FreeRADIUS server
5. Regularly rotate certificates
6. Monitor alerts for suspicious activity
7. Implement proper firewall rules
8. Enable audit logging and review regularly

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

## 🐛 Troubleshooting

### Common Issues

1. **Database connection failed**

   * Check PostgreSQL is running
   * Verify DATABASE_URL in .env
   * Check database credentials

2. **Certificate generation fails**

   * Verify CA certificates exist in `certificates/ca/`
   * Check file permissions

3. **Frontend cannot connect to backend**

   * Check CORS configuration
   * Verify backend is running

## 📚 Additional Resources

* FreeRADIUS Documentation
* Flask Documentation
* React Documentation
* Scapy Documentation

## 🤝 Contributing

1. Follow security best practices
2. Add tests for new features
3. Update documentation
4. Ensure code passes linting

## 📄 License

This project is for educational and enterprise demonstration purposes.

## 🎯 Use Cases

* Enterprise Network Access Control
* BYOD Security
* IoT Device Management
* Compliance Monitoring
* Security Auditing
* Incident Response

---

**Built for enterprise network security and cybersecurity education.**
