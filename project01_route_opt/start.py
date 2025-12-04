#!/usr/bin/env python3
"""
Startup script for Sahayog Route Optimizer
"""
import os
import sys
import subprocess
import time

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required.")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        'django',
        'ortools',
        'geopy',
        'PIL'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            else:
                __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them using: pip install -r requirements_simple.txt")
        return False
    
    return True

def run_migrations():
    """Run Django migrations."""
    print("\n🔄 Running database migrations...")
    try:
        subprocess.run([sys.executable, 'manage.py', 'migrate'], check=True)
        print("✅ Database migrations completed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Database migrations failed")
        return False

def create_superuser():
    """Create a superuser account."""
    print("\n👤 Creating superuser account...")
    print("Press Enter to skip or provide details:")
    
    username = input("Username (admin): ").strip() or "admin"
    email = input("Email: ").strip()
    password = input("Password: ").strip()
    
    if not password:
        print("❌ Password is required for superuser")
        return False
    
    try:
        # Create superuser using Django management command
        cmd = [sys.executable, 'manage.py', 'createsuperuser', '--noinput']
        env = os.environ.copy()
        env['DJANGO_SUPERUSER_USERNAME'] = username
        env['DJANGO_SUPERUSER_EMAIL'] = email
        env['DJANGO_SUPERUSER_PASSWORD'] = password
        
        subprocess.run(cmd, env=env, check=True)
        print(f"✅ Superuser '{username}' created successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create superuser")
        return False

def start_server():
    """Start the Django development server."""
    print("\n🚀 Starting development server...")
    print("Access the application at: http://localhost:8000/route-optimizer/")
    print("Admin panel at: http://localhost:8000/admin/")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run([sys.executable, 'manage.py', 'runserver'])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")

def main():
    """Main startup function."""
    print("🚀 Sahayog Route Optimizer - Startup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check dependencies
    print("\n📦 Checking dependencies...")
    if not check_dependencies():
        return
    
    # Run migrations
    if not run_migrations():
        return
    
    # Ask about superuser creation
    print("\n👤 Superuser Account")
    create_super = input("Create a superuser account? (y/n): ").strip().lower()
    if create_super in ['y', 'yes']:
        create_superuser()
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
