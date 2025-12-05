"""
Setup script to initialize the database and seed sample data.
Run this before starting the server for the first time.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.seed_data import seed_database

if __name__ == "__main__":
    print("Setting up Automated Waste Financial Ledger...")
    print("Creating database and seeding sample data...\n")
    
    try:
        seed_database()
        print("\n[SUCCESS] Setup complete!")
        print("\nNext steps:")
        print("1. Run 'py run_server.py' to start the API server")
        print("2. Open 'frontend/index.html' in your web browser")
        print("3. Use Company ID: C1234 to test the system")
    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        sys.exit(1)

