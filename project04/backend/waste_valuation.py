from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta
from typing import Dict, List

# Import models (will be available when running from project root)
try:
    from backend.models import WasteData, MaterialPrice, DisposalCost
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.models import WasteData, MaterialPrice, DisposalCost

class WasteValuationModule:
    """
    Core module for calculating Net Waste Value (NWV).
    
    Steps:
    A. Fetch recyclable material quantities, grades, and quality scores
    B. Request current, location-based material prices
    C. Retrieve non-recyclable and hazardous waste quantities
    D. Query disposal and landfill fee databases
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def fetch_recyclable_materials(self, company_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Step A: Fetch recyclable material data from real transactions."""
        from backend.models import WasteTransaction, WasteCategory
        
        # Try new transaction model first
        waste_records = self.db.query(
            func.sum(WasteTransaction.quantity_kg).label('total_quantity'),
            WasteTransaction.material_type,
            func.avg(WasteTransaction.quality_score).label('avg_quality'),
            func.max(WasteTransaction.grade).label('grade')
        ).filter(
            and_(
                WasteTransaction.company_id == company_id,
                WasteTransaction.material_category == WasteCategory.RECYCLABLE,
                WasteTransaction.transaction_date >= start_date,
                WasteTransaction.transaction_date <= end_date
            )
        ).group_by(WasteTransaction.material_type).all()
        
        # Debug: Log if no records found
        if not waste_records:
            # Check if any transactions exist at all for this company
            total_count = self.db.query(func.count(WasteTransaction.id)).filter(
                WasteTransaction.company_id == company_id
            ).scalar()
            if total_count == 0:
                print(f"Warning: No waste transactions found for company {company_id}")
            else:
                # Check date range
                earliest = self.db.query(func.min(WasteTransaction.transaction_date)).filter(
                    WasteTransaction.company_id == company_id
                ).scalar()
                latest = self.db.query(func.max(WasteTransaction.transaction_date)).filter(
                    WasteTransaction.company_id == company_id
                ).scalar()
                print(f"Warning: No recyclable transactions in date range. Company has transactions from {earliest} to {latest}, but querying {start_date} to {end_date}")
        
        if waste_records:
            return [
                {
                    "material_type": r.material_type,
                    "quantity_kg": float(r.total_quantity or 0),
                    "quality_score": float(r.avg_quality or 1.0),
                    "grade": r.grade or "A"
                }
                for r in waste_records
            ]
        
        # Fallback to old WasteData model for backward compatibility
        from backend.models import WasteData
        waste_records = self.db.query(
            func.sum(WasteData.quantity_kg).label('total_quantity'),
            WasteData.material_type,
            func.avg(WasteData.quality_score).label('avg_quality'),
            func.max(WasteData.grade).label('grade')
        ).filter(
            and_(
                WasteData.company_id == company_id,
                WasteData.material_category == "recyclable",
                WasteData.recorded_date >= start_date,
                WasteData.recorded_date <= end_date
            )
        ).group_by(WasteData.material_type).all()
        
        return [
            {
                "material_type": r.material_type,
                "quantity_kg": float(r.total_quantity or 0),
                "quality_score": float(r.avg_quality or 1.0),
                "grade": r.grade or "A"
            }
            for r in waste_records
        ]
    
    def get_material_prices(self, material_types: List[str], location: str, use_marketplace: bool = False) -> Dict[str, float]:
        """
        Step B: Get current location-based material prices.
        
        Can fetch from:
        1. Marketplace API (if use_marketplace=True and API is configured)
        2. Local database (default)
        3. Default fallback prices
        
        Args:
            material_types: List of material types to get prices for
            location: Geographic location
            use_marketplace: Whether to try marketplace API first (default: False)
        """
        prices = {}
        
        # Try marketplace API if enabled
        if use_marketplace:
            try:
                from backend.marketplace_api import MarketplaceAPI
                marketplace = MarketplaceAPI()
                marketplace_prices = marketplace.get_bulk_prices(material_types, location)
                prices.update(marketplace_prices)
            except Exception as e:
                print(f"Marketplace API not available, using database: {e}")
        
        # Get remaining prices from database
        for material_type in material_types:
            if material_type in prices:
                continue  # Already got from marketplace
            
            # Get the most recent active price for this material and location
            price_record = self.db.query(MaterialPrice).filter(
                and_(
                    MaterialPrice.material_type == material_type,
                    MaterialPrice.location == location,
                    MaterialPrice.is_active == True
                )
            ).order_by(MaterialPrice.effective_date.desc()).first()
            
            if price_record:
                prices[material_type] = price_record.price_per_kg
            else:
                # Default prices if not found (can be updated from external API)
                default_prices = {
                    "Cardboard": 12.0,
                    "Aluminum": 150.0,
                    "Plastic": 25.0,
                    "Glass": 8.0,
                    "Metal": 120.0,
                    "Paper": 15.0
                }
                prices[material_type] = default_prices.get(material_type, 10.0)
        
        return prices
    
    def fetch_non_recyclable_waste(self, company_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Step C: Retrieve non-recyclable and hazardous waste quantities."""
        from backend.models import WasteTransaction, WasteCategory
        
        # Try new transaction model first
        waste_records = self.db.query(
            func.sum(WasteTransaction.quantity_kg).label('total_quantity'),
            WasteTransaction.material_category
        ).filter(
            and_(
                WasteTransaction.company_id == company_id,
                WasteTransaction.material_category.in_([
                    WasteCategory.NON_RECYCLABLE, 
                    WasteCategory.HAZARDOUS,
                    WasteCategory.ORGANIC,
                    WasteCategory.ELECTRONIC
                ]),
                WasteTransaction.transaction_date >= start_date,
                WasteTransaction.transaction_date <= end_date
            )
        ).group_by(WasteTransaction.material_category).all()
        
        # Debug: Log if no records found
        if not waste_records:
            total_count = self.db.query(func.count(WasteTransaction.id)).filter(
                and_(
                    WasteTransaction.company_id == company_id,
                    WasteTransaction.material_category.in_([
                        WasteCategory.NON_RECYCLABLE, 
                        WasteCategory.HAZARDOUS,
                        WasteCategory.ORGANIC,
                        WasteCategory.ELECTRONIC
                    ])
                )
            ).scalar()
            if total_count > 0:
                earliest = self.db.query(func.min(WasteTransaction.transaction_date)).filter(
                    WasteTransaction.company_id == company_id
                ).scalar()
                latest = self.db.query(func.max(WasteTransaction.transaction_date)).filter(
                    WasteTransaction.company_id == company_id
                ).scalar()
                print(f"Warning: No non-recyclable transactions in date range. Company has transactions from {earliest} to {latest}, but querying {start_date} to {end_date}")
        
        if waste_records:
            return [
                {
                    "category": r.material_category.value if hasattr(r.material_category, 'value') else str(r.material_category),
                    "quantity_kg": float(r.total_quantity or 0)
                }
                for r in waste_records
            ]
        
        # Fallback to old model
        from backend.models import WasteData
        waste_records = self.db.query(
            func.sum(WasteData.quantity_kg).label('total_quantity'),
            WasteData.material_category
        ).filter(
            and_(
                WasteData.company_id == company_id,
                WasteData.material_category.in_(["non_recyclable", "hazardous"]),
                WasteData.recorded_date >= start_date,
                WasteData.recorded_date <= end_date
            )
        ).group_by(WasteData.material_category).all()
        
        return [
            {
                "category": r.material_category,
                "quantity_kg": float(r.total_quantity or 0)
            }
            for r in waste_records
        ]
    
    def get_disposal_costs(self, categories: List[str], location: str) -> Dict[str, float]:
        """Step D: Query disposal and landfill fee databases."""
        costs = {}
        
        for category in categories:
            # Get the most recent active disposal cost
            cost_record = self.db.query(DisposalCost).filter(
                and_(
                    DisposalCost.waste_category == category,
                    DisposalCost.location == location,
                    DisposalCost.is_active == True
                )
            ).order_by(DisposalCost.effective_date.desc()).first()
            
            if cost_record:
                costs[category] = cost_record.cost_per_kg
            else:
                # Default costs if not found
                default_costs = {
                    "non_recyclable": 5.0,
                    "hazardous": 25.0,
                    "landfill": 8.0
                }
                costs[category] = default_costs.get(category, 5.0)
        
        return costs
    
    def calculate_revenue(self, recyclable_materials: List[Dict], prices: Dict[str, float]) -> Dict:
        """Calculate total revenue from recyclables."""
        revenue_breakdown = []
        total_revenue = 0.0
        
        for material in recyclable_materials:
            material_type = material["material_type"]
            quantity = material["quantity_kg"]
            quality = material["quality_score"]
            price_per_kg = prices.get(material_type, 0.0)
            
            # Apply quality adjustment (higher quality = better price)
            adjusted_price = price_per_kg * quality
            material_revenue = quantity * adjusted_price
            
            revenue_breakdown.append({
                "material": material_type,
                "quantity_kg": round(quantity, 2),
                "price_per_kg": round(adjusted_price, 2),
                "value": round(material_revenue, 2),
                "quality_score": round(quality, 2)
            })
            
            total_revenue += material_revenue
        
        return {
            "total_revenue": round(total_revenue, 2),
            "breakdown": sorted(revenue_breakdown, key=lambda x: x["value"], reverse=True)
        }
    
    def calculate_costs(self, non_recyclable_waste: List[Dict], disposal_costs: Dict[str, float]) -> Dict:
        """Calculate total disposal costs."""
        cost_breakdown = []
        total_cost = 0.0
        
        for waste in non_recyclable_waste:
            category = waste["category"]
            quantity = waste["quantity_kg"]
            cost_per_kg = disposal_costs.get(category, 0.0)
            
            category_cost = quantity * cost_per_kg
            
            # Map category to display name
            display_name = {
                "non_recyclable": "Landfill",
                "hazardous": "Hazardous Waste",
                "landfill": "Landfill"
            }.get(category, category.title())
            
            cost_breakdown.append({
                "type": display_name,
                "quantity_kg": round(quantity, 2),
                "cost_per_kg": round(cost_per_kg, 2),
                "value": round(category_cost, 2)
            })
            
            total_cost += category_cost
        
        return {
            "total_cost": round(total_cost, 2),
            "breakdown": sorted(cost_breakdown, key=lambda x: x["value"], reverse=True)
        }
    
    def generate_recommendations(self, revenue_data: Dict, cost_data: Dict, nwv: float) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Find top revenue generator
        if revenue_data["breakdown"]:
            top_material = revenue_data["breakdown"][0]
            material_name = top_material["material"]
            current_value = top_material["value"]
            
            # Suggest improvement in segregation
            potential_increase = current_value * 0.2  # 20% improvement
            recommendations.append(
                f"Improve segregation of {material_name} by 20% to increase net value by ₹{potential_increase:,.0f}/month."
            )
        
        # Cost reduction suggestions
        if cost_data["breakdown"]:
            highest_cost = cost_data["breakdown"][0]
            cost_type = highest_cost["type"]
            cost_value = highest_cost["value"]
            
            if cost_value > 5000:
                recommendations.append(
                    f"Focus on reducing {cost_type} disposal (currently ₹{cost_value:,.0f}). "
                    f"Consider waste reduction strategies or alternative disposal methods."
                )
        
        # NWV-based recommendations
        if nwv < 0:
            recommendations.append(
                f"Current Net Waste Value is negative (₹{abs(nwv):,.0f}). "
                f"Prioritize increasing recyclable waste collection and improving material quality."
            )
        elif nwv > 0:
            recommendations.append(
                f"Excellent! Net Waste Value is positive. "
                f"Consider scaling up recycling operations to maximize revenue."
            )
        
        # Vendor negotiation suggestion
        if revenue_data["breakdown"]:
            recommendations.append(
                "Negotiate local scrap price updates with vendors to raise revenue."
            )
        
        return recommendations
    
    def compare_with_historical(self, company_id: str, current_start: datetime, current_end: datetime) -> Dict:
        """Compare current period with previous period of same duration."""
        # Calculate period duration
        period_days = (current_end - current_start).days + 1
        
        # Calculate previous period dates
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=period_days - 1)
        
        # Get company info
        from backend.models import Company
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return None
        
        location = company.location
        
        # Fetch previous period data
        prev_recyclable = self.fetch_recyclable_materials(company_id, previous_start, previous_end)
        prev_non_recyclable = self.fetch_non_recyclable_waste(company_id, previous_start, previous_end)
        
        # Get prices and costs (use same as current period)
        prev_material_types = [m["material_type"] for m in prev_recyclable]
        prev_prices = self.get_material_prices(prev_material_types, location)
        prev_waste_categories = [w["category"] for w in prev_non_recyclable]
        prev_disposal_costs = self.get_disposal_costs(prev_waste_categories, location)
        
        # Calculate previous period metrics
        prev_revenue_data = self.calculate_revenue(prev_recyclable, prev_prices)
        prev_cost_data = self.calculate_costs(prev_non_recyclable, prev_disposal_costs)
        prev_nwv = prev_revenue_data["total_revenue"] - prev_cost_data["total_cost"]
        
        return {
            "previous_period": {
                "start_date": previous_start.isoformat(),
                "end_date": previous_end.isoformat(),
                "total_revenue": prev_revenue_data["total_revenue"],
                "total_cost": prev_cost_data["total_cost"],
                "net_waste_value": round(prev_nwv, 2)
            }
        }
    
    def generate_report(self, company_id: str, start_date: datetime, end_date: datetime, compare_historical: bool = False, use_marketplace: bool = False) -> Dict:
        """Main method to generate complete financial report."""
        # Get company info
        from backend.models import Company
        
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError(f"Company {company_id} not found")
        
        location = company.location
        
        # Step A: Fetch recyclable materials (with audit quality scores from segregation audit)
        recyclable_materials = self.fetch_recyclable_materials(company_id, start_date, end_date)
        
        # Step B: Get material prices (from marketplace API or database)
        material_types = [m["material_type"] for m in recyclable_materials]
        prices = self.get_material_prices(material_types, location, use_marketplace=use_marketplace)
        
        # Step C: Fetch non-recyclable waste
        non_recyclable_waste = self.fetch_non_recyclable_waste(company_id, start_date, end_date)
        
        # Step D: Get disposal costs
        waste_categories = [w["category"] for w in non_recyclable_waste]
        disposal_costs = self.get_disposal_costs(waste_categories, location)
        
        # Calculate revenue (this is expected revenue from calculations)
        revenue_data = self.calculate_revenue(recyclable_materials, prices)
        
        # Calculate costs
        cost_data = self.calculate_costs(non_recyclable_waste, disposal_costs)
        
        # Fetch all individual transactions for detailed breakdown (needed early for revenue entries)
        from backend.models import WasteTransaction, WasteCategory, RevenueEntry
        all_transactions = self.db.query(WasteTransaction).filter(
            and_(
                WasteTransaction.company_id == company_id,
                WasteTransaction.transaction_date >= start_date,
                WasteTransaction.transaction_date <= end_date
            )
        ).order_by(WasteTransaction.transaction_date.desc()).all()
        
        # Fetch revenue entries for these transactions
        transaction_ids = [txn.id for txn in all_transactions]
        revenue_entries = {}
        revenue_entry_list = []  # Keep list of all entry objects for data quality
        if transaction_ids:
            entries = self.db.query(RevenueEntry).filter(
                RevenueEntry.transaction_id.in_(transaction_ids)
            ).all()
            revenue_entry_list = entries  # Store all entries
            # Group by transaction_id - use the latest entry per transaction
            for entry in entries:
                if entry.transaction_id not in revenue_entries:
                    revenue_entries[entry.transaction_id] = []
                revenue_entries[entry.transaction_id].append(entry)
            # For each transaction, use the sum of all revenue entries (in case of multiple entries)
            for txn_id in revenue_entries:
                entries_list = revenue_entries[txn_id]
                total_actual_revenue = sum(e.actual_revenue for e in entries_list)
                revenue_entries[txn_id] = total_actual_revenue
        
        # Fetch cost entries for these transactions
        from backend.models import CostEntry
        cost_entries = {}
        cost_entry_list = []  # Keep list of all entry objects for data quality
        if transaction_ids:
            entries = self.db.query(CostEntry).filter(
                CostEntry.transaction_id.in_(transaction_ids)
            ).all()
            cost_entry_list = entries  # Store all entries
            # Group by transaction_id - sum all cost entries per transaction
            for entry in entries:
                if entry.transaction_id not in cost_entries:
                    cost_entries[entry.transaction_id] = []
                cost_entries[entry.transaction_id].append(entry)
            # For each transaction, use the sum of all cost entries
            for txn_id in cost_entries:
                entries_list = cost_entries[txn_id]
                total_actual_cost = sum(e.actual_cost for e in entries_list)
                cost_entries[txn_id] = total_actual_cost
        
        # Calculate total actual revenue from revenue entries (sum all actual revenues)
        total_actual_revenue = sum(revenue_entries.values()) if revenue_entries else 0.0
        
        # Calculate total expected revenue (sum of all transaction calculated revenues)
        total_expected_revenue = sum(txn.total_revenue or 0.0 for txn in all_transactions)
        
        # Calculate total actual cost from cost entries (sum all actual costs)
        total_actual_cost = sum(cost_entries.values()) if cost_entries else 0.0
        
        # Calculate total expected cost (sum of all transaction calculated costs)
        total_expected_cost = sum(txn.disposal_cost or 0.0 for txn in all_transactions)
        
        # Use actual revenue if available, otherwise use calculated revenue
        display_revenue = total_actual_revenue if total_actual_revenue > 0 else total_expected_revenue
        
        # Use actual cost if available, otherwise use calculated
        display_cost = total_actual_cost if total_actual_cost > 0 else total_expected_cost
        
        # Calculate Net Waste Value using effective revenue and cost (needed for historical comparison and recommendations)
        nwv = display_revenue - display_cost
        
        # Historical comparison
        historical_comparison = None
        if compare_historical:
            historical_comparison = self.compare_with_historical(company_id, start_date, end_date)
            if historical_comparison:
                prev_nwv = historical_comparison["previous_period"]["net_waste_value"]
                nwv_change = nwv - prev_nwv
                nwv_change_percent = (nwv_change / abs(prev_nwv) * 100) if prev_nwv != 0 else 0
                historical_comparison["nwv_change"] = round(nwv_change, 2)
                historical_comparison["nwv_change_percent"] = round(nwv_change_percent, 2)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(revenue_data, cost_data, nwv)
        
        # Add historical insights to recommendations
        if historical_comparison and historical_comparison.get("nwv_change"):
            change = historical_comparison["nwv_change"]
            change_percent = historical_comparison["nwv_change_percent"]
            if change > 0:
                recommendations.insert(0, 
                    f"NWV improved by ₹{abs(change):,.0f} ({abs(change_percent):.1f}%) compared to previous period. "
                    f"Continue current waste management practices."
                )
            elif change < 0:
                recommendations.insert(0,
                    f"NWV decreased by ₹{abs(change):,.0f} ({abs(change_percent):.1f}%) compared to previous period. "
                    f"Review waste segregation and disposal processes."
                )
        
        # Format report period
        report_period = start_date.strftime("%B %Y")
        if start_date.month != end_date.month or start_date.year != end_date.year:
            report_period = f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"
        
        transactions_summary = []
        for txn in all_transactions:
            # Use actual revenue from revenue entries if available, otherwise use transaction's calculated revenue
            actual_revenue = revenue_entries.get(txn.id, None)
            if actual_revenue is not None:
                display_revenue = round(actual_revenue, 2)
            else:
                display_revenue = round(txn.total_revenue, 2) if txn.total_revenue else 0.0
            
            # Use actual cost from cost entries if available, otherwise use transaction's calculated cost
            actual_cost = cost_entries.get(txn.id, None)
            if actual_cost is not None:
                display_cost = round(actual_cost, 2)
            else:
                display_cost = round(txn.disposal_cost, 2) if txn.disposal_cost else 0.0
            
            transactions_summary.append({
                "id": txn.id,
                "date": txn.transaction_date.strftime("%Y-%m-%d %H:%M"),
                "material_type": txn.material_type,
                "category": txn.material_category.value if hasattr(txn.material_category, 'value') else str(txn.material_category),
                "quantity_kg": round(txn.quantity_kg, 2),
                "quality_score": round(txn.quality_score, 2) if txn.quality_score else None,
                "revenue": display_revenue,
                "expected_revenue": round(txn.total_revenue, 2) if txn.total_revenue else 0.0,
                "has_revenue_entry": txn.id in revenue_entries,
                "cost": display_cost,
                "expected_cost": round(txn.disposal_cost, 2) if txn.disposal_cost else 0.0,
                "has_cost_entry": txn.id in cost_entries,
                "net_value": round(display_revenue - display_cost, 2),
                "collection_point": txn.collection_point.name if txn.collection_point else None
            })
        
        # Material-wise summary (grouped by material type) - ALL transactions
        # Use actual revenue from revenue entries when available
        material_summary = {}
        for txn in all_transactions:
            mat_type = txn.material_type
            if mat_type not in material_summary:
                material_summary[mat_type] = {
                    "material_type": mat_type,
                    "total_quantity_kg": 0.0,
                    "total_revenue": 0.0,
                    "total_expected_revenue": 0.0,
                    "total_cost": 0.0,
                    "transaction_count": 0,
                    "categories": set(),
                    "avg_quality": []
                }
            material_summary[mat_type]["total_quantity_kg"] += txn.quantity_kg
            # Use actual revenue if available, otherwise use expected
            actual_rev = revenue_entries.get(txn.id, None)
            if actual_rev is not None:
                material_summary[mat_type]["total_revenue"] += actual_rev
            else:
                material_summary[mat_type]["total_revenue"] += (txn.total_revenue or 0)
            material_summary[mat_type]["total_expected_revenue"] += (txn.total_revenue or 0)
            # Use actual cost if available, otherwise use expected
            actual_cost = cost_entries.get(txn.id, None)
            if actual_cost is not None:
                material_summary[mat_type]["total_cost"] += actual_cost
            else:
                material_summary[mat_type]["total_cost"] += (txn.disposal_cost or 0)
            material_summary[mat_type]["transaction_count"] += 1
            if txn.quality_score:
                material_summary[mat_type]["avg_quality"].append(txn.quality_score)
            if txn.material_category:
                cat_val = txn.material_category.value if hasattr(txn.material_category, 'value') else str(txn.material_category)
                material_summary[mat_type]["categories"].add(cat_val)
        
        # Convert to list and format - Include ALL materials
        material_summary_list = []
        for mat_type, data in material_summary.items():
            avg_quality = sum(data["avg_quality"]) / len(data["avg_quality"]) if data["avg_quality"] else 1.0
            material_summary_list.append({
                "material_type": mat_type,
                "total_quantity_kg": round(data["total_quantity_kg"], 2),
                "total_revenue": round(data["total_revenue"], 2),
                "total_expected_revenue": round(data["total_expected_revenue"], 2),
                "total_cost": round(data["total_cost"], 2),
                "net_value": round(data["total_revenue"] - data["total_cost"], 2),
                "transaction_count": data["transaction_count"],
                "categories": list(data["categories"]),
                "avg_quality": round(avg_quality, 2)
            })
        # Sort by total revenue first, then by net value
        material_summary_list.sort(key=lambda x: (x["total_revenue"], x["net_value"]), reverse=True)
        
        # Category-wise summary - Use actual revenue from revenue entries
        category_summary = {}
        for txn in all_transactions:
            cat = txn.material_category.value if hasattr(txn.material_category, 'value') else str(txn.material_category)
            if cat not in category_summary:
                category_summary[cat] = {
                    "category": cat,
                    "total_quantity_kg": 0.0,
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                    "transaction_count": 0
                }
            category_summary[cat]["total_quantity_kg"] += txn.quantity_kg
            # Use actual revenue if available
            actual_rev = revenue_entries.get(txn.id, None)
            if actual_rev is not None:
                category_summary[cat]["total_revenue"] += actual_rev
            else:
                category_summary[cat]["total_revenue"] += (txn.total_revenue or 0)
            # Use actual cost if available
            actual_cost = cost_entries.get(txn.id, None)
            if actual_cost is not None:
                category_summary[cat]["total_cost"] += actual_cost
            else:
                category_summary[cat]["total_cost"] += (txn.disposal_cost or 0)
            category_summary[cat]["transaction_count"] += 1
        
        category_summary_list = [
            {
                "category": cat,
                "total_quantity_kg": round(data["total_quantity_kg"], 2),
                "total_revenue": round(data["total_revenue"], 2),
                "total_cost": round(data["total_cost"], 2),
                "net_value": round(data["total_revenue"] - data["total_cost"], 2),
                "transaction_count": data["transaction_count"]
            }
            for cat, data in category_summary.items()
        ]
        category_summary_list.sort(key=lambda x: x["net_value"], reverse=True)
        
        # Time-based trend data (daily aggregation) - Use actual revenue
        daily_trends = {}
        for txn in all_transactions:
            date_key = txn.transaction_date.strftime("%Y-%m-%d")
            if date_key not in daily_trends:
                daily_trends[date_key] = {
                    "date": date_key,
                    "revenue": 0.0,
                    "cost": 0.0,
                    "transactions": 0
                }
            # Use actual revenue if available
            actual_rev = revenue_entries.get(txn.id, None)
            if actual_rev is not None:
                daily_trends[date_key]["revenue"] += actual_rev
            else:
                daily_trends[date_key]["revenue"] += (txn.total_revenue or 0)
            # Use actual cost if available
            actual_cost = cost_entries.get(txn.id, None)
            if actual_cost is not None:
                daily_trends[date_key]["cost"] += actual_cost
            else:
                daily_trends[date_key]["cost"] += (txn.disposal_cost or 0)
            daily_trends[date_key]["transactions"] += 1
        
        daily_trends_list = sorted([
            {
                "date": data["date"],
                "revenue": round(data["revenue"], 2),
                "cost": round(data["cost"], 2),
                "net_value": round(data["revenue"] - data["cost"], 2),
                "transactions": data["transactions"]
            }
            for data in daily_trends.values()
        ], key=lambda x: x["date"])
        
        # Build revenue breakdown from ALL transactions (not just recyclable)
        # Use material_summary which includes ALL materials - show ALL materials even if revenue is 0
        # Use actual revenue from revenue entries
        revenue_chart_data = []
        for mat in material_summary_list:
            # Include ALL materials - even if revenue is 0, show them with 0 value
            # Use actual revenue (which already includes revenue entries)
            revenue_chart_data.append({
                "material": mat["material_type"],
                "value": mat["total_revenue"],  # This already uses actual revenue from entries
                "expected_value": mat.get("total_expected_revenue", mat["total_revenue"]),
                "quantity": mat["total_quantity_kg"],
                "transactions": mat["transaction_count"]
            })
        # Sort by value descending (materials with revenue first)
        revenue_chart_data.sort(key=lambda x: x["value"], reverse=True)
        
        # Build cost breakdown from ALL transactions (not just non-recyclable)
        # Use category_summary which includes all categories with costs
        cost_chart_data = []
        for cat in category_summary_list:
            if cat["total_cost"] > 0:
                cost_chart_data.append({
                    "type": cat["category"],
                    "value": cat["total_cost"]
                })
        # Sort by value descending
        cost_chart_data.sort(key=lambda x: x["value"], reverse=True)
        
        # If no daily trends (single day), create at least one data point
        if not daily_trends_list and all_transactions:
            # Aggregate all transactions into one day
            total_rev = sum(txn.total_revenue or 0 for txn in all_transactions)
            total_cost = sum(txn.disposal_cost or 0 for txn in all_transactions)
            daily_trends_list = [{
                "date": all_transactions[0].transaction_date.strftime("%Y-%m-%d"),
                "revenue": round(total_rev, 2),
                "cost": round(total_cost, 2),
                "net_value": round(total_rev - total_cost, 2),
                "transactions": len(all_transactions)
            }]
        
        # Expanded KPI calculations
        total_quantity = sum(txn.quantity_kg for txn in all_transactions)
        recyclable_quantity = sum(
            txn.quantity_kg for txn in all_transactions
            if txn.material_category == WasteCategory.RECYCLABLE
        )
        hazardous_quantity = sum(
            txn.quantity_kg for txn in all_transactions
            if txn.material_category == WasteCategory.HAZARDOUS
        )
        organic_quantity = sum(
            txn.quantity_kg for txn in all_transactions
            if txn.material_category == WasteCategory.ORGANIC
        )
        electronic_quantity = sum(
            txn.quantity_kg for txn in all_transactions
            if txn.material_category == WasteCategory.ELECTRONIC
        )
        diversion_rate = (recyclable_quantity / total_quantity * 100.0) if total_quantity else 0.0
        hazardous_ratio = (hazardous_quantity / total_quantity * 100.0) if total_quantity else 0.0
        
        quality_weighted_sum = 0.0
        quality_weight = 0.0
        contamination_weighted_sum = 0.0
        contamination_weight = 0.0
        max_contamination = 0.0
        low_quality_transactions = 0
        for txn in all_transactions:
            if txn.quality_score is not None:
                quality_weighted_sum += txn.quality_score * txn.quantity_kg
                quality_weight += txn.quantity_kg
                if txn.quality_score < 0.85:
                    low_quality_transactions += 1
            if txn.contamination_level is not None:
                contamination_weighted_sum += txn.contamination_level * txn.quantity_kg
                contamination_weight += txn.quantity_kg
                max_contamination = max(max_contamination, txn.contamination_level)
        average_quality = (quality_weighted_sum / quality_weight) if quality_weight else 1.0
        average_contamination = (contamination_weighted_sum / contamination_weight) if contamination_weight else 0.0
        
        revenue_per_kg = (revenue_data["total_revenue"] / total_quantity) if total_quantity else 0.0
        cost_per_kg = (cost_data["total_cost"] / total_quantity) if total_quantity else 0.0
        net_per_kg = ((revenue_data["total_revenue"] - cost_data["total_cost"]) / total_quantity) if total_quantity else 0.0
        
        # Collection point summary
        collection_points_summary = {}
        for txn in all_transactions:
            key = txn.collection_point.name if txn.collection_point else "Unassigned"
            if key not in collection_points_summary:
                collection_points_summary[key] = {
                    "collection_point": key,
                    "total_quantity_kg": 0.0,
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                    "net_value": 0.0,
                    "transaction_count": 0
                }
            cp_entry = collection_points_summary[key]
            cp_entry["total_quantity_kg"] += txn.quantity_kg
            cp_entry["total_revenue"] += (txn.total_revenue or 0)
            cp_entry["total_cost"] += (txn.disposal_cost or 0)
            cp_entry["net_value"] += ((txn.total_revenue or 0) - (txn.disposal_cost or 0))
            cp_entry["transaction_count"] += 1
        collection_points_list = [
            {
                "collection_point": name,
                "total_quantity_kg": round(data["total_quantity_kg"], 2),
                "total_revenue": round(data["total_revenue"], 2),
                "total_cost": round(data["total_cost"], 2),
                "net_value": round(data["net_value"], 2),
                "transaction_count": data["transaction_count"]
            }
            for name, data in collection_points_summary.items()
        ]
        collection_points_list.sort(key=lambda x: x["net_value"], reverse=True)
        
        # Identify top / bottom performers
        top_material = material_summary_list[0] if material_summary_list else None
        bottom_material = material_summary_list[-1] if material_summary_list else None
        
        # Risk alerts based on operational indicators
        risk_alerts = []
        if diversion_rate < 50 and total_quantity:
            risk_alerts.append(
                "Recycling diversion rate is below 50%. Increase recyclable capture to avoid landfill penalties."
            )
        if average_quality < 0.85:
            risk_alerts.append(
                f"Average quality score dropped to {average_quality:.2f}. Review segregation SOPs at source."
            )
        if average_contamination > 0.2:
            risk_alerts.append(
                f"Average contamination level is {average_contamination:.2f}. Additional sorting or supplier feedback recommended."
            )
        if cost_data["total_cost"] > revenue_data["total_revenue"]:
            risk_alerts.append(
                "Disposal cost exceeds recycling revenue in this period. Investigate high-cost waste streams."
            )
        if max_contamination > 0.4:
            risk_alerts.append(
                "One or more transactions recorded contamination above 40%. Ensure hazardous handling compliance."
            )
        if hazardous_ratio > 10:
            risk_alerts.append(
                "Hazardous waste proportion exceeded 10% of total volume. Validate treatment protocols and vendor certifications."
            )
        
        # Calculate advanced analytical metrics
        # Revenue variance analysis
        revenue_variance = total_actual_revenue - total_expected_revenue if total_actual_revenue > 0 else 0
        revenue_variance_percent = (revenue_variance / total_expected_revenue * 100) if total_expected_revenue > 0 else 0
        
        # Cost variance analysis
        cost_variance = total_actual_cost - total_expected_cost if total_actual_cost > 0 else 0
        cost_variance_percent = (cost_variance / total_expected_cost * 100) if total_expected_cost > 0 else 0
        
        # Profitability metrics
        profit_margin = (nwv / display_revenue * 100) if display_revenue > 0 else 0
        cost_efficiency_ratio = (display_revenue / display_cost) if display_cost > 0 else 0
        roi_percentage = ((nwv - display_cost) / display_cost * 100) if display_cost > 0 else 0
        
        # Material profitability analysis
        material_profitability = {}
        for mat_data in material_summary_list:
            mat_revenue = mat_data["total_revenue"]
            mat_cost = mat_data["total_cost"]
            mat_qty = mat_data["total_quantity_kg"]
            mat_profit_margin = (mat_data["net_value"] / mat_revenue * 100) if mat_revenue > 0 else 0
            mat_revenue_per_kg = (mat_revenue / mat_qty) if mat_qty > 0 else 0
            mat_cost_per_kg = (mat_cost / mat_qty) if mat_qty > 0 else 0
            
            material_profitability[mat_data["material_type"]] = {
                "profit_margin_percent": round(mat_profit_margin, 2),
                "revenue_per_kg": round(mat_revenue_per_kg, 2),
                "cost_per_kg": round(mat_cost_per_kg, 2),
                "net_value_per_kg": round(mat_data["net_value"] / mat_qty, 2) if mat_qty > 0 else 0,
                "profitability_score": round((mat_profit_margin + mat_revenue_per_kg / 100), 2)  # Combined score
            }
        
        # Performance efficiency metrics
        avg_transaction_value = (display_revenue / len(all_transactions)) if all_transactions else 0
        avg_transaction_cost = (display_cost / len(all_transactions)) if all_transactions else 0
        avg_transaction_nwv = (nwv / len(all_transactions)) if all_transactions else 0
        
        # Waste processing efficiency
        recyclable_efficiency = (recyclable_quantity / total_quantity * 100) if total_quantity > 0 else 0
        revenue_efficiency = (display_revenue / total_quantity) if total_quantity > 0 else 0
        
        # Time-based performance (if daily trends available)
        performance_trend = "stable"
        if len(daily_trends_list) >= 2:
            first_half_nwv = sum(d["net_value"] for d in daily_trends_list[:len(daily_trends_list)//2])
            second_half_nwv = sum(d["net_value"] for d in daily_trends_list[len(daily_trends_list)//2:])
            if second_half_nwv > first_half_nwv * 1.1:
                performance_trend = "improving"
            elif second_half_nwv < first_half_nwv * 0.9:
                performance_trend = "declining"
        
        # Quality impact on revenue
        high_quality_transactions = [txn for txn in all_transactions if txn.quality_score and txn.quality_score >= 0.8]
        high_quality_revenue = sum(revenue_entries.get(txn.id, txn.total_revenue or 0) for txn in high_quality_transactions)
        quality_revenue_ratio = (high_quality_revenue / display_revenue * 100) if display_revenue > 0 else 0
        
        # Cost breakdown analysis - only show if we have actual breakdown data from CostEntry
        cost_breakdown_analysis = {}
        if cost_entries and transaction_ids:
            # Fetch cost entries for breakdown
            cost_entry_objects = self.db.query(CostEntry).filter(
                CostEntry.transaction_id.in_(transaction_ids)
            ).all()
            
            # Only calculate breakdown if cost entries have breakdown fields filled
            disposal_total = sum(e.disposal_cost or 0.0 for e in cost_entry_objects if e.disposal_cost)
            transport_total = sum(e.transportation_cost or 0.0 for e in cost_entry_objects if e.transportation_cost)
            processing_total = sum(e.processing_cost or 0.0 for e in cost_entry_objects if e.processing_cost)
            other_total = sum(e.other_costs or 0.0 for e in cost_entry_objects if e.other_costs)
            
            # Calculate total breakdown cost (sum of all breakdown fields)
            total_breakdown_cost = disposal_total + transport_total + processing_total + other_total
            
            # Only show breakdown if we have breakdown data AND it matches actual costs
            # If breakdown totals don't match actual_cost, use actual_cost as denominator
            if total_breakdown_cost > 0:
                # Use breakdown total as denominator for accurate percentages
                breakdown_denominator = total_breakdown_cost
                
                cost_breakdown_analysis = {
                    "disposal_percentage": round((disposal_total / breakdown_denominator * 100) if breakdown_denominator > 0 else 0, 2),
                    "transportation_percentage": round((transport_total / breakdown_denominator * 100) if breakdown_denominator > 0 else 0, 2),
                    "processing_percentage": round((processing_total / breakdown_denominator * 100) if breakdown_denominator > 0 else 0, 2),
                    "other_percentage": round((other_total / breakdown_denominator * 100) if breakdown_denominator > 0 else 0, 2),
                    "disposal_amount": round(disposal_total, 2),
                    "transportation_amount": round(transport_total, 2),
                    "processing_amount": round(processing_total, 2),
                    "other_amount": round(other_total, 2),
                    "total_breakdown_cost": round(total_breakdown_cost, 2),
                    "has_breakdown_data": True
                }
            else:
                # No breakdown data available - mark as such
                cost_breakdown_analysis = {
                    "has_breakdown_data": False,
                    "message": "Cost breakdown data not available. Add cost entries with breakdown details (disposal, transportation, processing, other costs)."
                }
        
        # Benchmark comparisons - Calculate from historical data if available, otherwise use industry estimates
        # Try to get historical averages from this company's past data
        historical_transactions = self.db.query(WasteTransaction).filter(
            and_(
                WasteTransaction.company_id == company_id,
                WasteTransaction.transaction_date < start_date  # Before current period
            )
        ).limit(100).all()  # Get last 100 transactions
        
        if historical_transactions and len(historical_transactions) > 0:
            # Calculate actual historical averages
            hist_revenues = [t.total_revenue or 0.0 for t in historical_transactions]
            hist_costs = [t.disposal_cost or 0.0 for t in historical_transactions]
            hist_quantities = [t.quantity_kg for t in historical_transactions]
            
            hist_total_revenue = sum(hist_revenues)
            hist_total_cost = sum(hist_costs)
            hist_total_qty = sum(hist_quantities)
            
            hist_revenue_per_kg = (hist_total_revenue / hist_total_qty) if hist_total_qty > 0 else 50.0
            hist_cost_per_kg = (hist_total_cost / hist_total_qty) if hist_total_qty > 0 else 15.0
            hist_profit_margin = ((hist_total_revenue - hist_total_cost) / hist_total_revenue * 100) if hist_total_revenue > 0 else 70.0
            
            # Use historical data as benchmarks (calculated from company's own data)
            industry_benchmarks = {
                "avg_revenue_per_kg": hist_revenue_per_kg,
                "avg_cost_per_kg": hist_cost_per_kg,
                "avg_profit_margin": hist_profit_margin,
                "avg_diversion_rate": 60.0,  # Keep industry standard for diversion rate
                "is_calculated": True,  # Mark as calculated from company data
                "historical_transactions_count": len(historical_transactions)
            }
        else:
            # Fallback to industry estimates (clearly marked as estimates)
            industry_benchmarks = {
                "avg_revenue_per_kg": 50.0,  # Industry estimate
                "avg_cost_per_kg": 15.0,  # Industry estimate
                "avg_profit_margin": 70.0,  # Industry estimate
                "avg_diversion_rate": 60.0,  # Industry estimate
                "is_calculated": False,  # Mark as industry estimates
                "historical_transactions_count": 0
            }
        
        benchmark_comparison = {
            "revenue_per_kg_vs_industry": round(revenue_per_kg - industry_benchmarks["avg_revenue_per_kg"], 2),
            "cost_per_kg_vs_industry": round(cost_per_kg - industry_benchmarks["avg_cost_per_kg"], 2),
            "profit_margin_vs_industry": round(profit_margin - industry_benchmarks["avg_profit_margin"], 2),
            "diversion_rate_vs_industry": round(diversion_rate - industry_benchmarks["avg_diversion_rate"], 2),
            "performance_rating": "excellent" if profit_margin > 75 and diversion_rate > 70 else 
                                 "good" if profit_margin > 60 and diversion_rate > 50 else
                                 "average" if profit_margin > 40 and diversion_rate > 40 else "needs_improvement",
            "is_calculated": industry_benchmarks.get("is_calculated", False),
            "historical_transactions_count": industry_benchmarks.get("historical_transactions_count", 0),
            "benchmark_source": "company_historical" if industry_benchmarks.get("is_calculated", False) else "industry_estimate"
        }
        
        # Note: total_actual_revenue, total_expected_revenue, display_revenue, and nwv 
        # are already calculated above before historical comparison and recommendations
        
        report = {
            "company_id": company_id,
            "company_name": company.name,
            "report_period": report_period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_revenue": round(display_revenue, 2),
            "total_expected_revenue": round(total_expected_revenue, 2),
            "total_actual_revenue": round(total_actual_revenue, 2),
            "total_cost": round(display_cost, 2),
            "total_expected_cost": round(total_expected_cost, 2),
            "total_actual_cost": round(total_actual_cost, 2),
            "net_waste_value": round(nwv, 2),
            "total_transactions": len(all_transactions),
            "recommendations": recommendations,
            "charts": {
                "revenue_breakdown": revenue_chart_data,  # Use ALL materials with revenue
                "cost_breakdown": cost_chart_data,  # Use ALL categories with costs
                "daily_trends": daily_trends_list
            },
            "detailed_revenue": revenue_data["breakdown"],
            "detailed_costs": cost_data["breakdown"],
            "transactions": transactions_summary,
            "material_summary": material_summary_list,
            "category_summary": category_summary_list,
            "kpi_summary": {
                "total_quantity_kg": round(total_quantity, 2),
                "recyclable_quantity_kg": round(recyclable_quantity, 2),
                "diversion_rate_percent": round(diversion_rate, 2),
                "hazardous_ratio_percent": round(hazardous_ratio, 2),
                "revenue_per_kg": round(revenue_per_kg, 2),
                "cost_per_kg": round(cost_per_kg, 2),
                "net_value_per_kg": round(net_per_kg, 2)
            },
            "quality_metrics": {
                "average_quality_score": round(average_quality, 2),
                "average_contamination_level": round(average_contamination, 2),
                "max_contamination_level": round(max_contamination, 2),
                "transactions_below_quality_threshold": low_quality_transactions
            },
            "collection_points": collection_points_list,
            "top_material": top_material,
            "bottom_material": bottom_material,
            "risk_alerts": risk_alerts,
            # NEW: Advanced Analytical Metrics
            "variance_analysis": {
                "revenue_variance": round(revenue_variance, 2),
                "revenue_variance_percent": round(revenue_variance_percent, 2),
                "cost_variance": round(cost_variance, 2),
                "cost_variance_percent": round(cost_variance_percent, 2),
                "net_variance_impact": round(revenue_variance - cost_variance, 2)
            },
            "profitability_metrics": {
                "profit_margin_percent": round(profit_margin, 2),
                "cost_efficiency_ratio": round(cost_efficiency_ratio, 2),
                "roi_percentage": round(roi_percentage, 2),
                "revenue_efficiency_per_kg": round(revenue_efficiency, 2)
            },
            "material_profitability": material_profitability,
            "performance_metrics": {
                "avg_transaction_value": round(avg_transaction_value, 2),
                "avg_transaction_cost": round(avg_transaction_cost, 2),
                "avg_transaction_nwv": round(avg_transaction_nwv, 2),
                "recyclable_efficiency_percent": round(recyclable_efficiency, 2),
                "performance_trend": performance_trend,
                "quality_revenue_ratio_percent": round(quality_revenue_ratio, 2)
            },
            "cost_breakdown_analysis": cost_breakdown_analysis,
            "benchmark_comparison": benchmark_comparison,
            # Data Quality Indicators
            "data_quality": {
                "revenue_entries_count": len(revenue_entry_list) if revenue_entry_list else 0,
                "cost_entries_count": len(cost_entry_list) if cost_entry_list else 0,
                "transactions_with_revenue": len([txn_id for txn_id in revenue_entries.keys() if revenue_entries[txn_id] > 0]),
                "transactions_with_costs": len([txn_id for txn_id in cost_entries.keys() if cost_entries[txn_id] > 0]),
                "data_completeness_percent": round(
                    ((len([txn_id for txn_id in revenue_entries.keys() if revenue_entries[txn_id] > 0]) + 
                      len([txn_id for txn_id in cost_entries.keys() if cost_entries[txn_id] > 0])) / 
                     (len(all_transactions) * 2) * 100) if all_transactions and len(all_transactions) > 0 else 0, 2
                )
            }
        }
        
        # Add historical comparison if requested
        if historical_comparison:
            report["historical_comparison"] = historical_comparison
        
        return report

