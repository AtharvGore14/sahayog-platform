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
        
        # Calculate revenue
        revenue_data = self.calculate_revenue(recyclable_materials, prices)
        
        # Calculate costs
        cost_data = self.calculate_costs(non_recyclable_waste, disposal_costs)
        
        # Calculate Net Waste Value
        nwv = revenue_data["total_revenue"] - cost_data["total_cost"]
        
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
        
        # Fetch all individual transactions for detailed breakdown
        from backend.models import WasteTransaction, WasteCategory
        all_transactions = self.db.query(WasteTransaction).filter(
            and_(
                WasteTransaction.company_id == company_id,
                WasteTransaction.transaction_date >= start_date,
                WasteTransaction.transaction_date <= end_date
            )
        ).order_by(WasteTransaction.transaction_date.desc()).all()
        
        transactions_summary = []
        for txn in all_transactions:
            transactions_summary.append({
                "id": txn.id,
                "date": txn.transaction_date.strftime("%Y-%m-%d %H:%M"),
                "material_type": txn.material_type,
                "category": txn.material_category.value if hasattr(txn.material_category, 'value') else str(txn.material_category),
                "quantity_kg": round(txn.quantity_kg, 2),
                "quality_score": round(txn.quality_score, 2) if txn.quality_score else None,
                "revenue": round(txn.total_revenue, 2) if txn.total_revenue else 0.0,
                "cost": round(txn.disposal_cost, 2) if txn.disposal_cost else 0.0,
                "net_value": round((txn.total_revenue or 0) - (txn.disposal_cost or 0), 2),
                "collection_point": txn.collection_point.name if txn.collection_point else None
            })
        
        # Material-wise summary (grouped by material type) - ALL transactions
        material_summary = {}
        for txn in all_transactions:
            mat_type = txn.material_type
            if mat_type not in material_summary:
                material_summary[mat_type] = {
                    "material_type": mat_type,
                    "total_quantity_kg": 0.0,
                    "total_revenue": 0.0,
                    "total_cost": 0.0,
                    "transaction_count": 0,
                    "categories": set(),
                    "avg_quality": []
                }
            material_summary[mat_type]["total_quantity_kg"] += txn.quantity_kg
            material_summary[mat_type]["total_revenue"] += (txn.total_revenue or 0)
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
                "total_cost": round(data["total_cost"], 2),
                "net_value": round(data["total_revenue"] - data["total_cost"], 2),
                "transaction_count": data["transaction_count"],
                "categories": list(data["categories"]),
                "avg_quality": round(avg_quality, 2)
            })
        # Sort by total revenue first, then by net value
        material_summary_list.sort(key=lambda x: (x["total_revenue"], x["net_value"]), reverse=True)
        
        # Category-wise summary
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
            category_summary[cat]["total_revenue"] += (txn.total_revenue or 0)
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
        
        # Time-based trend data (daily aggregation)
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
            daily_trends[date_key]["revenue"] += (txn.total_revenue or 0)
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
        revenue_chart_data = []
        for mat in material_summary_list:
            # Include ALL materials - even if revenue is 0, show them with 0 value
            revenue_chart_data.append({
                "material": mat["material_type"],
                "value": mat["total_revenue"],
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
        
        # Build final report with comprehensive data
        report = {
            "company_id": company_id,
            "company_name": company.name,
            "report_period": report_period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_revenue": revenue_data["total_revenue"],
            "total_cost": cost_data["total_cost"],
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
            "risk_alerts": risk_alerts
        }
        
        # Add historical comparison if requested
        if historical_comparison:
            report["historical_comparison"] = historical_comparison
        
        return report

