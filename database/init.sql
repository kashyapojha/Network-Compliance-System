-- PostgreSQL initialization (schema is created by SQLAlchemy on backend startup)
-- Do not store passwords or secrets in this file.

\c network_compliance;

-- Grant permissions to the application database user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO CURRENT_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO CURRENT_USER;

-- Create the first admin via the API after deployment:
--   POST /api/auth/register  { "username", "email", "password" }
