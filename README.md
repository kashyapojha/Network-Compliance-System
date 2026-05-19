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
