"""
Waste Data Entry Module - Handles real-time waste transaction entry and processing
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime
from typing import Dict, List, Optional
from backend.models import (
    WasteTransaction, CollectionPoint, Company, 
    MaterialPrice, DisposalCost, SegregationAudit, WasteCategory
)

class WasteEntryService:
    """Service for entering and processing waste transactions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_waste_transaction(
        self,
        company_id: str,
        material_type: str,
        material_category: str,
        quantity_kg: float,
        collection_point_id: Optional[int] = None,
        quality_score: Optional[float] = None,
        grade: Optional[str] = None,
        contamination_level: Optional[float] = None,
        transaction_date: Optional[datetime] = None,
        recorded_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """Create a new waste transaction with automatic price/cost calculation"""
        
        # Validate company exists
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        # Validate collection point if provided
        if collection_point_id:
            cp = self.db.query(CollectionPoint).filter(
                and_(
                    CollectionPoint.id == collection_point_id,
                    CollectionPoint.company_id == company_id
                )
            ).first()
            if not cp:
                raise ValueError(f"Collection point {collection_point_id} not found for company")
        
        # Validate category
        try:
            category = WasteCategory(material_category.lower())
        except ValueError:
            raise ValueError(f"Invalid material category: {material_category}")
        
        # Get quality score from latest audit if not provided
        if quality_score is None:
            quality_score = self._get_latest_quality_score(company_id, collection_point_id)
        
        # Calculate financial values
        unit_price = None
        total_revenue = 0.0
        disposal_cost = 0.0
        
        if category == WasteCategory.RECYCLABLE:
            # Get current market price
            price_record = self._get_current_price(material_type, company.location, grade)
            if price_record:
                unit_price = price_record.price_per_kg
                # Apply quality adjustment
                adjusted_price = unit_price * (quality_score or 1.0)
                total_revenue = quantity_kg * adjusted_price
        else:
            # Get disposal cost
            cost_record = self._get_current_disposal_cost(category.value, company.location)
            if cost_record:
                disposal_cost = quantity_kg * cost_record.cost_per_kg
        
        # Create transaction
        transaction = WasteTransaction(
            company_id=company_id,
            collection_point_id=collection_point_id,
            transaction_date=transaction_date or datetime.utcnow(),
            material_type=material_type,
            material_category=category,
            quantity_kg=quantity_kg,
            quality_score=quality_score or 1.0,
            grade=grade,
            contamination_level=contamination_level or 0.0,
            unit_price=unit_price,
            total_revenue=total_revenue,
            disposal_cost=disposal_cost,
            recorded_by=recorded_by,
            notes=notes
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return {
            "transaction_id": transaction.id,
            "company_id": company_id,
            "material_type": material_type,
            "quantity_kg": quantity_kg,
            "total_revenue": total_revenue,
            "disposal_cost": disposal_cost,
            "net_value": total_revenue - disposal_cost,
            "transaction_date": transaction.transaction_date.isoformat()
        }
    
    def _get_latest_quality_score(self, company_id: str, collection_point_id: Optional[int]) -> float:
        """Get latest quality score from segregation audit"""
        query = self.db.query(SegregationAudit).filter(
            SegregationAudit.company_id == company_id
        )
        
        if collection_point_id:
            query = query.filter(SegregationAudit.collection_point_id == collection_point_id)
        
        latest_audit = query.order_by(SegregationAudit.audit_date.desc()).first()
        
        if latest_audit:
            return latest_audit.segregation_quality_score
        
        return 1.0  # Default perfect score
    
    def _get_current_price(self, material_type: str, location: str, grade: Optional[str]) -> Optional[MaterialPrice]:
        """Get current market price for material"""
        query = self.db.query(MaterialPrice).filter(
            and_(
                MaterialPrice.material_type == material_type,
                MaterialPrice.location == location,
                MaterialPrice.is_active == True
            )
        )
        
        if grade:
            query = query.filter(
                (MaterialPrice.grade_requirement == None) | 
                (MaterialPrice.grade_requirement == grade)
            )
        
        return query.order_by(MaterialPrice.effective_date.desc()).first()
    
    def _get_current_disposal_cost(self, category: str, location: str) -> Optional[DisposalCost]:
        """Get current disposal cost for waste category"""
        return self.db.query(DisposalCost).filter(
            and_(
                DisposalCost.waste_category == category,
                DisposalCost.location == location,
                DisposalCost.is_active == True
            )
        ).order_by(DisposalCost.effective_date.desc()).first()
    
    def bulk_import_transactions(self, transactions: List[Dict]) -> Dict:
        """Import multiple transactions at once"""
        results = {
            "successful": [],
            "failed": [],
            "total_count": len(transactions)
        }
        
        for txn_data in transactions:
            try:
                result = self.create_waste_transaction(**txn_data)
                results["successful"].append(result)
            except Exception as e:
                results["failed"].append({
                    "data": txn_data,
                    "error": str(e)
                })
        
        return results
    
    def get_transactions(
        self,
        company_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        collection_point_id: Optional[int] = None,
        material_type: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve waste transactions with filters"""
        query = self.db.query(WasteTransaction).filter(
            WasteTransaction.company_id == company_id
        )
        
        if start_date:
            query = query.filter(WasteTransaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(WasteTransaction.transaction_date <= end_date)
        if collection_point_id:
            query = query.filter(WasteTransaction.collection_point_id == collection_point_id)
        if material_type:
            query = query.filter(WasteTransaction.material_type == material_type)
        
        transactions = query.order_by(WasteTransaction.transaction_date.desc()).all()
        
        return [
            {
                "id": t.id,
                "transaction_date": t.transaction_date.isoformat(),
                "material_type": t.material_type,
                "material_category": t.material_category.value,
                "quantity_kg": t.quantity_kg,
                "quality_score": t.quality_score,
                "grade": t.grade,
                "total_revenue": t.total_revenue,
                "disposal_cost": t.disposal_cost,
                "net_value": t.total_revenue - t.disposal_cost,
                "collection_point": t.collection_point.name if t.collection_point else None
            }
            for t in transactions
        ]

