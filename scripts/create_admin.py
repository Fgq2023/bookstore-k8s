#!/usr/bin/env python3
"""
Create admin user in the bookstore database.
Run this inside the backend pod.

Usage:
    kubectl exec -it -n bookstore deployment/bookstore-backend -- python3 /tmp/create_admin.py
"""

import os
import sys

# Try to import psycopg2 directly (should be available in backend pod)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from werkzeug.security import generate_password_hash
except ImportError as e:
    print(f"Error: {e}")
    print("This script must run inside the backend pod where dependencies are installed.")
    sys.exit(1)

# Configuration - adjust if your DB credentials differ
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'bookstore-db'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'bookstore'),
    'user': os.getenv('POSTGRES_USER', 'bookstore_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'SecureP@ssw0rd!2026'),
}

# Admin user details
ADMIN_USERNAME = 'admin'
ADMIN_EMAIL = 'admin@bookstore.com'
ADMIN_PASSWORD = 'admin123'

def create_admin_user():
    """Create an admin user if it doesn't exist."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check if admin user already exists
        cur.execute("SELECT id, username, is_admin FROM users WHERE username = %s", (ADMIN_USERNAME,))
        existing = cur.fetchone()
        
        if existing:
            print(f"Admin user already exists:")
            print(f"  ID: {existing['id']}")
            print(f"  Username: {existing['username']}")
            print(f"  Is Admin: {existing['is_admin']}")
            
            # Ensure is_admin is True
            if not existing['is_admin']:
                cur.execute("UPDATE users SET is_admin = true WHERE id = %s", (existing['id'],))
                conn.commit()
                print("  Updated: Set is_admin = true")
            
            cur.close()
            conn.close()
            return
        
        # Create admin user
        password_hash = generate_password_hash(ADMIN_PASSWORD)
        cur.execute("""
            INSERT INTO users (username, email, password_hash, is_admin)
            VALUES (%s, %s, %s, %s)
            RETURNING id, username, is_admin
        """, (ADMIN_USERNAME, ADMIN_EMAIL, password_hash, True))
        
        user = cur.fetchone()
        conn.commit()
        
        print("Admin user created successfully!")
        print(f"  ID: {user['id']}")
        print(f"  Username: {user['username']}")
        print(f"  Email: {ADMIN_EMAIL}")
        print(f"  Password: {ADMIN_PASSWORD}")
        print(f"  Is Admin: {user['is_admin']}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin_user()
