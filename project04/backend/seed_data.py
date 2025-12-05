"""
Script to seed the database with sample data for testing.
"""
from backend.database import SessionLocal, engine, Base
from backend.models import Company, WasteData, MaterialPrice, DisposalCost
from datetime import datetime, timedelta
import random
import os

# Drop all tables first to ensure clean schema
print("Dropping existing tables...")
Base.metadata.drop_all(bind=engine)

# Create tables with new schema
print("Creating tables with updated schema...")
Base.metadata.create_all(bind=engine)

def seed_database():
    db = SessionLocal()
    
    try:
        # Create sample company
        company = Company(
            id="C1234",
            name="TechCorp Industries",
            location="Mumbai",
            industry_type="Manufacturing"
        )
        db.add(company)
        db.commit()
        
        # Create sample collection points
        from backend.models import CollectionPoint
        cp1 = CollectionPoint(
            company_id="C1234",
            name="Warehouse A",
            location="Building 1, Floor 2"
        )
        cp2 = CollectionPoint(
            company_id="C1234",
            name="Production Floor B",
            location="Building 2, Floor 1"
        )
        db.add(cp1)
        db.add(cp2)
        db.commit()
        
        # Create material prices
        materials = [
            ("Cardboard", 12.0),
            ("Aluminum", 150.0),
            ("Plastic", 25.0),
            ("Glass", 8.0),
            ("Metal", 120.0),
            ("Paper", 15.0)
        ]
        
        for material_type, price in materials:
            price_record = MaterialPrice(
                material_type=material_type,
                location="Mumbai",
                price_per_kg=price,
                effective_date=datetime.now(),
                is_active=True
            )
            db.add(price_record)
        
        # Create disposal costs
        disposal_types = [
            ("non_recyclable", 5.0),
            ("hazardous", 25.0),
            ("landfill", 8.0),
            ("organic", 3.0),  # Composting cost
            ("electronic", 30.0)  # E-waste disposal cost
        ]
        
        for category, cost in disposal_types:
            cost_record = DisposalCost(
                waste_category=category,
                location="Mumbai",
                cost_per_kg=cost,
                effective_date=datetime.now(),
                is_active=True
            )
            db.add(cost_record)
        
        db.commit()
        
        # Create waste transactions for current month using new transaction model
        from backend.models import WasteTransaction, WasteCategory
        
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        
        # Recyclable materials - create as transactions
        recyclable_data = [
            ("Cardboard", 750.0, 0.9, "A", WasteCategory.RECYCLABLE),
            ("Aluminum", 33.3, 0.95, "A", WasteCategory.RECYCLABLE),
            ("Plastic", 180.0, 0.85, "B", WasteCategory.RECYCLABLE),
            ("Metal", 50.0, 0.92, "A", WasteCategory.RECYCLABLE),
        ]
        
        for material_type, quantity, quality, grade, category in recyclable_data:
            for i in range(5):  # 5 records per material
                # Get price for revenue calculation
                price_record = db.query(MaterialPrice).filter(
                    MaterialPrice.material_type == material_type,
                    MaterialPrice.location == "Mumbai",
                    MaterialPrice.is_active == True
                ).first()
                
                unit_price = price_record.price_per_kg if price_record else 10.0
                adjusted_price = unit_price * quality
                total_revenue = (quantity / 5) * adjusted_price
                
                transaction = WasteTransaction(
                    company_id="C1234",
                    collection_point_id=cp1.id if i % 2 == 0 else cp2.id,
                    transaction_date=start_of_month + timedelta(days=random.randint(0, now.day)),
                    material_type=material_type,
                    material_category=category,
                    quantity_kg=quantity / 5,
                    quality_score=quality + random.uniform(-0.1, 0.1),
                    grade=grade,
                    contamination_level=1.0 - quality,
                    unit_price=unit_price,
                    total_revenue=total_revenue,
                    disposal_cost=0.0,
                    recorded_by="System"
                )
                db.add(transaction)
        
        # Non-recyclable waste
        non_recyclable_data = [
            ("Mixed Waste", 2000.0, WasteCategory.NON_RECYCLABLE),
            ("Organic Waste", 1500.0, WasteCategory.ORGANIC),
        ]
        
        for material_type, quantity, category in non_recyclable_data:
            for i in range(10):
                # Get disposal cost
                cost_record = db.query(DisposalCost).filter(
                    DisposalCost.waste_category == category.value,
                    DisposalCost.location == "Mumbai",
                    DisposalCost.is_active == True
                ).first()
                
                cost_per_kg = cost_record.cost_per_kg if cost_record else 5.0
                disposal_cost = (quantity / 10) * cost_per_kg
                
                transaction = WasteTransaction(
                    company_id="C1234",
                    collection_point_id=cp1.id if i % 2 == 0 else cp2.id,
                    transaction_date=start_of_month + timedelta(days=random.randint(0, now.day)),
                    material_type=material_type,
                    material_category=category,
                    quantity_kg=quantity / 10,
                    quality_score=0.5,
                    grade=None,
                    contamination_level=0.5,
                    unit_price=None,
                    total_revenue=0.0,
                    disposal_cost=disposal_cost,
                    recorded_by="System"
                )
                db.add(transaction)
        
        # Hazardous waste
        cost_record = db.query(DisposalCost).filter(
            DisposalCost.waste_category == "hazardous",
            DisposalCost.location == "Mumbai",
            DisposalCost.is_active == True
        ).first()
        
        cost_per_kg = cost_record.cost_per_kg if cost_record else 25.0
        hazardous_transaction = WasteTransaction(
            company_id="C1234",
            collection_point_id=cp1.id,
            transaction_date=start_of_month + timedelta(days=5),
            material_type="Electronics",
            material_category=WasteCategory.HAZARDOUS,
            quantity_kg=320.0,
            quality_score=0.3,
            grade=None,
            contamination_level=0.7,
            unit_price=None,
            total_revenue=0.0,
            disposal_cost=320.0 * cost_per_kg,
            recorded_by="System"
        )
        db.add(hazardous_transaction)
        
        # Create a segregation audit
        from backend.models import SegregationAudit
        audit = SegregationAudit(
            company_id="C1234",
            collection_point_id=cp1.id,
            segregation_quality_score=0.85,
            contamination_percentage=0.15,
            proper_labeling_score=0.90,
            compliance_score=0.88,
            issues_found="Minor contamination in cardboard bins",
            recommendations="Improve training on proper segregation",
            auditor_name="System"
        )
        db.add(audit)
        
        db.commit()
        print("Database seeded successfully!")
        print(f"Company ID: C1234")
        print(f"Location: Mumbai")
        print(f"Sample data created for {now.strftime('%B %Y')}")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()

