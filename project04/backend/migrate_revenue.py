"""
Migration script to add RevenueEntry table to the database
Run this script to add the revenue tracking feature to existing databases
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.models import RevenueEntry

def migrate():
    """Create RevenueEntry table if it doesn't exist"""
    print("🔄 Starting migration: Adding RevenueEntry table...")
    
    try:
        # Create all tables (will only create new ones)
        Base.metadata.create_all(bind=engine)
        print("✅ Migration completed successfully!")
        print("📊 RevenueEntry table is now available for revenue tracking")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()

