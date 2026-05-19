-- Initialize database with default admin user
-- This script runs when PostgreSQL container starts for the first time

\c network_compliance;

-- Create default admin user (password: admin123)
-- Note: In production, change this password immediately
INSERT INTO admins (username, email, hashed_password, role, is_active)
VALUES (
    'admin',
    'admin@enterprise.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYqXqXqXqXqX', -- bcrypt hash of 'admin123'
    'admin',
    true
);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
