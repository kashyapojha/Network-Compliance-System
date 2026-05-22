# Environment setup (repository root `.env`)

Create **`.env`** next to `README.md`. Use only `KEY=value` lines (no Markdown).

```env
SECRET_KEY=
JWT_SECRET_KEY=
DEBUG=True
PORT=5000
DATABASE_URL=
POSTGRES_DB=network_compliance
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
VITE_SOCKET_URL=http://localhost:5000
NETWORK_RANGE=
POLL_INTERVAL=30
AUTO_START_MONITORING=true
BACKEND_URL=http://localhost:5000
SMTP_ENABLED=false
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
ADMIN_EMAIL=
```

`AUTO_START_MONITORING=true` runs network scans in the background.  
`SMTP_ENABLED=true` sends email when a new unknown device is detected.
