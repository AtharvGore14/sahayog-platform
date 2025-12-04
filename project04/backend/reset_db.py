"""
Script to completely reset the database - drops all tables and recreates them
"""
import os
import sys
from backend.database import engine, Base

# Import all models to ensure they're registered
from backend.models import (
    Company, WasteData, MaterialPrice, DisposalCost,
    WasteTransaction, CollectionPoint, SegregationAudit,
    NWVForecast, CostOptimization
)

def reset_database():
    """Drop all tables and recreate with new schema"""
    print("=" * 50)
    print("RESETTING DATABASE")
    print("=" * 50)
    print()
    
    # Check if database file exists
    db_file = "waste_ledger.db"
    
    try:
        # Drop all tables
        print("Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ Tables dropped")
    except Exception as e:
        print(f"Warning: Could not drop tables: {e}")
        if os.path.exists(db_file):
            print("Trying to delete database file...")
            try:
                os.remove(db_file)
                print("✓ Database file deleted")
            except Exception as e2:
                print(f"✗ Cannot delete database file: {e2}")
                print("\nERROR: Database file is locked!")
                print("The server may still be running.")
                return False
    
    # Create all tables with new schema
    print("\nCreating tables with updated schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")
        print("\nSchema includes:")
        print("  - companies (with industry_type)")
        print("  - waste_transactions")
        print("  - collection_points")
        print("  - segregation_audits")
        print("  - material_prices")
        print("  - disposal_costs")
        print("  - nwv_forecasts")
        print("  - cost_optimizations")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = reset_database()
    if success:
        print("\n" + "=" * 50)
        print("Database reset complete!")
        print("=" * 50)
        print("\nNow run: py setup.py")
    else:
        print("\n" + "=" * 50)
        print("Reset failed. Please ensure server is stopped.")
        print("=" * 50)
        sys.exit(1)
