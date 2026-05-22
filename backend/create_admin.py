#!/usr/bin/env python3
"""Create default admin user and initialize database."""

import sys
import os

# Add backend directory to path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

from app.database import init_db, SessionLocal
from app.models.admin import Admin, UserRole
from app.utils.auth import hash_password

def main():
    """Initialize database and create default admin user."""
    print("Initializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing_admin = db.query(Admin).filter(Admin.username == 'admin').first()
        if existing_admin:
            print("Admin user already exists. Skipping creation.")
            return
        
        # Create default admin user
        admin = Admin(
            username='admin',
            email='admin@ultratech.com',
            hashed_password=hash_password('admin123'),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin)
        db.commit()
        
        print("Default admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("\nPlease change the password after first login.")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()
