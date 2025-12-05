"""
Migration script to add CostEntry table to the database
Run this script to add the cost tracking feature to existing databases
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import engine, Base
from backend.models import CostEntry

def migrate():
    """Create CostEntry table if it doesn't exist"""
    print("🔄 Starting migration: Adding CostEntry table...")
    
    try:
        # Create all tables (will only create new ones)
        Base.metadata.create_all(bind=engine)
        print("✅ Migration completed successfully!")
        print("📊 CostEntry table is now available for cost tracking")
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    migrate()

