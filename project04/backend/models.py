from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from backend.database import Base
from datetime import datetime
import enum

class WasteCategory(str, enum.Enum):
    RECYCLABLE = "recyclable"
    NON_RECYCLABLE = "non_recyclable"
    HAZARDOUS = "hazardous"
    ORGANIC = "organic"
    ELECTRONIC = "electronic"

class CollectionPoint(Base):
    __tablename__ = "collection_points"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "Warehouse A", "Production Floor B"
    location = Column(String, nullable=False)  # Physical location within company
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    waste_transactions = relationship("WasteTransaction", back_populates="collection_point")
    audits = relationship("SegregationAudit", back_populates="collection_point")

class Company(Base):
    __tablename__ = "companies"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    industry_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    waste_transactions = relationship("WasteTransaction", back_populates="company")
    collection_points = relationship("CollectionPoint", back_populates="company")
    audits = relationship("SegregationAudit", back_populates="company")

# Fix relationships
CollectionPoint.company = relationship("Company", back_populates="collection_points")

class WasteTransaction(Base):
    """Real waste transactions - actual data entry"""
    __tablename__ = "waste_transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    collection_point_id = Column(Integer, ForeignKey("collection_points.id"), nullable=True)
    
    # Transaction details
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    material_type = Column(String, nullable=False, index=True)
    material_category = Column(SQLEnum(WasteCategory), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    
    # Quality metrics
    quality_score = Column(Float, default=1.0)  # 0.0 to 1.0 - from audit
    grade = Column(String, nullable=True)  # "A", "B", "C"
    contamination_level = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Financial data (calculated)
    unit_price = Column(Float, nullable=True)  # Price per kg at time of transaction
    total_revenue = Column(Float, default=0.0)  # Calculated revenue
    disposal_cost = Column(Float, default=0.0)  # Disposal cost if applicable
    
    # Metadata
    recorded_by = Column(String, nullable=True)  # User/system who recorded
    notes = Column(Text, nullable=True)
    batch_number = Column(String, nullable=True)  # For tracking batches
    
    # Relationships
    company = relationship("Company", back_populates="waste_transactions")
    collection_point = relationship("CollectionPoint", back_populates="waste_transactions")

class SegregationAudit(Base):
    """Waste segregation quality audits"""
    __tablename__ = "segregation_audits"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    collection_point_id = Column(Integer, ForeignKey("collection_points.id"), nullable=True)
    
    audit_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    auditor_name = Column(String, nullable=True)
    
    # Audit scores
    segregation_quality_score = Column(Float, nullable=False)  # 0.0 to 1.0
    contamination_percentage = Column(Float, default=0.0)
    proper_labeling_score = Column(Float, default=1.0)
    compliance_score = Column(Float, default=1.0)
    
    # Findings
    issues_found = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    corrective_actions = Column(Text, nullable=True)
    
    # Relationships
    company = relationship("Company", back_populates="audits")
    collection_point = relationship("CollectionPoint", back_populates="audits")

# Keep old WasteData for backward compatibility
class WasteData(Base):
    __tablename__ = "waste_data"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    material_type = Column(String, nullable=False)
    material_category = Column(String, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    quality_score = Column(Float, default=1.0)
    grade = Column(String, nullable=True)
    recorded_date = Column(DateTime, default=datetime.utcnow, nullable=False)

class MaterialPrice(Base):
    __tablename__ = "material_prices"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_type = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    effective_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)
    source = Column(String, nullable=True)  # "marketplace", "vendor", "database"
    min_quantity_kg = Column(Float, default=0.0)  # Minimum quantity for this price
    grade_requirement = Column(String, nullable=True)  # Required grade (A, B, C)

class DisposalCost(Base):
    __tablename__ = "disposal_costs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    waste_category = Column(String, nullable=False)
    location = Column(String, nullable=False)
    cost_per_kg = Column(Float, nullable=False)
    effective_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True)
    vendor_name = Column(String, nullable=True)
    min_quantity_kg = Column(Float, default=0.0)  # Minimum quantity for this cost

class NWVForecast(Base):
    """Forecasted NWV values for future periods"""
    __tablename__ = "nwv_forecasts"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    forecast_date = Column(DateTime, nullable=False, index=True)
    forecast_period_start = Column(DateTime, nullable=False)
    forecast_period_end = Column(DateTime, nullable=False)
    
    predicted_revenue = Column(Float, nullable=False)
    predicted_cost = Column(Float, nullable=False)
    predicted_nwv = Column(Float, nullable=False)
    
    confidence_level = Column(Float, default=0.8)  # 0.0 to 1.0
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CostOptimization(Base):
    """Cost optimization recommendations"""
    __tablename__ = "cost_optimizations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    company_id = Column(String, ForeignKey("companies.id"), nullable=False)
    generated_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    optimization_type = Column(String, nullable=False)  # "segregation", "vendor", "volume", "material"
    current_cost = Column(Float, nullable=False)
    optimized_cost = Column(Float, nullable=False)
    potential_savings = Column(Float, nullable=False)
    
    recommendation = Column(Text, nullable=False)
    implementation_difficulty = Column(String, nullable=True)  # "low", "medium", "high"
    estimated_implementation_time = Column(String, nullable=True)
    status = Column(String, default="pending")  # "pending", "implemented", "rejected"
