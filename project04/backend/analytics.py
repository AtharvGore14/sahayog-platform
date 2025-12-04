"""
Advanced Analytics Module - Forecasting, Trends, and Cost Optimization
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import statistics
from backend.models import (
    WasteTransaction, Company, NWVForecast, CostOptimization, 
    MaterialPrice, DisposalCost, SegregationAudit
)

class AnalyticsEngine:
    """Advanced analytics and forecasting engine"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_trends(self, company_id: str, days: int = 30) -> Dict:
        """Calculate trends over specified period"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily NWV
        daily_nwv = self._get_daily_nwv(company_id, start_date, end_date)
        
        # Always return daily_data for chart display, even if insufficient for trend analysis
        result = {
            "period_days": days,
            "daily_data": daily_nwv
        }
        
        if len(daily_nwv) == 0:
            result["error"] = "No data found for this period"
            return result
        
        if len(daily_nwv) < 2:
            # Still return data for chart, but mark as insufficient for trend analysis
            result["error"] = "Insufficient data for trend analysis (need at least 2 days)"
            result["average_nwv"] = round(daily_nwv[0]["nwv"], 2) if daily_nwv else 0
            result["peak_nwv"] = round(daily_nwv[0]["nwv"], 2) if daily_nwv else 0
            result["lowest_nwv"] = round(daily_nwv[0]["nwv"], 2) if daily_nwv else 0
            result["trend_direction"] = "stable"
            result["trend_percentage"] = 0.0
            return result
        
        # Calculate trend direction
        first_half = daily_nwv[:len(daily_nwv)//2]
        second_half = daily_nwv[len(daily_nwv)//2:]
        
        avg_first = statistics.mean([d["nwv"] for d in first_half])
        avg_second = statistics.mean([d["nwv"] for d in second_half])
        
        trend_direction = "improving" if avg_second > avg_first else "declining"
        trend_percentage = ((avg_second - avg_first) / abs(avg_first) * 100) if avg_first != 0 else 0
        
        result.update({
            "trend_direction": trend_direction,
            "trend_percentage": round(trend_percentage, 2),
            "average_nwv": round(statistics.mean([d["nwv"] for d in daily_nwv]), 2),
            "peak_nwv": round(max([d["nwv"] for d in daily_nwv]), 2),
            "lowest_nwv": round(min([d["nwv"] for d in daily_nwv]), 2)
        })
        
        return result
    
    def _get_daily_nwv(self, company_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get daily NWV values"""
        transactions = self.db.query(WasteTransaction).filter(
            and_(
                WasteTransaction.company_id == company_id,
                WasteTransaction.transaction_date >= start_date,
                WasteTransaction.transaction_date <= end_date
            )
        ).all()
        
        print(f"[Analytics] Found {len(transactions)} transactions for {company_id} between {start_date} and {end_date}")
        
        # Group by date
        daily_data = {}
        for txn in transactions:
            date_key = txn.transaction_date.date()
            if date_key not in daily_data:
                daily_data[date_key] = {"revenue": 0.0, "cost": 0.0}
            
            daily_data[date_key]["revenue"] += (txn.total_revenue or 0.0)
            daily_data[date_key]["cost"] += (txn.disposal_cost or 0.0)
        
        result = [
            {
                "date": str(date),
                "revenue": round(data["revenue"], 2),
                "cost": round(data["cost"], 2),
                "nwv": round(data["revenue"] - data["cost"], 2)
            }
            for date, data in sorted(daily_data.items())
        ]
        
        print(f"[Analytics] Returning {len(result)} days of data")
        return result
    
    def forecast_nwv(
        self,
        company_id: str,
        forecast_days: int = 30,
        method: str = "moving_average"
    ) -> Dict:
        """Forecast future NWV using various methods"""
        
        # Get historical data (last 90 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        daily_nwv = self._get_daily_nwv(company_id, start_date, end_date)
        
        if len(daily_nwv) < 7:
            return {"error": "Insufficient historical data for forecasting"}
        
        nwv_values = [d["nwv"] for d in daily_nwv]
        
        if method == "moving_average":
            # Simple moving average forecast
            window = min(7, len(nwv_values))
            recent_avg = statistics.mean(nwv_values[-window:])
            
            forecast_nwv = recent_avg * forecast_days
            forecast_revenue = statistics.mean([d["revenue"] for d in daily_nwv[-window:]]) * forecast_days
            forecast_cost = statistics.mean([d["cost"] for d in daily_nwv[-window:]]) * forecast_days
            
        elif method == "linear_trend":
            # Linear regression (simplified)
            if len(nwv_values) >= 2:
                x = list(range(len(nwv_values)))
                slope = (nwv_values[-1] - nwv_values[0]) / len(nwv_values) if len(nwv_values) > 1 else 0
                intercept = nwv_values[-1] - slope * len(nwv_values)
                
                forecast_nwv = (slope * (len(nwv_values) + forecast_days) + intercept) * forecast_days
                forecast_revenue = statistics.mean([d["revenue"] for d in daily_nwv[-7:]]) * forecast_days
                forecast_cost = statistics.mean([d["cost"] for d in daily_nwv[-7:]]) * forecast_days
            else:
                forecast_nwv = statistics.mean(nwv_values) * forecast_days
                forecast_revenue = statistics.mean([d["revenue"] for d in daily_nwv]) * forecast_days
                forecast_cost = statistics.mean([d["cost"] for d in daily_nwv]) * forecast_days
        else:
            # Default to simple average
            forecast_nwv = statistics.mean(nwv_values) * forecast_days
            forecast_revenue = statistics.mean([d["revenue"] for d in daily_nwv]) * forecast_days
            forecast_cost = statistics.mean([d["cost"] for d in daily_nwv]) * forecast_days
        
        # Calculate confidence based on data consistency
        std_dev = statistics.stdev(nwv_values) if len(nwv_values) > 1 else 0
        mean_val = statistics.mean(nwv_values)
        coefficient_of_variation = (std_dev / abs(mean_val)) if mean_val != 0 else 1.0
        confidence = max(0.5, min(0.95, 1.0 - coefficient_of_variation))
        
        # Save forecast
        forecast_start = end_date + timedelta(days=1)
        forecast_end = end_date + timedelta(days=forecast_days)
        
        forecast_record = NWVForecast(
            company_id=company_id,
            forecast_date=datetime.utcnow(),
            forecast_period_start=forecast_start,
            forecast_period_end=forecast_end,
            predicted_revenue=forecast_revenue,
            predicted_cost=forecast_cost,
            predicted_nwv=forecast_nwv,
            confidence_level=confidence,
            model_version=method
        )
        
        self.db.add(forecast_record)
        self.db.commit()
        
        return {
            "forecast_period_days": forecast_days,
            "forecast_start": forecast_start.isoformat(),
            "forecast_end": forecast_end.isoformat(),
            "predicted_revenue": round(forecast_revenue, 2),
            "predicted_cost": round(forecast_cost, 2),
            "predicted_nwv": round(forecast_nwv, 2),
            "forecasted_nwv": round(forecast_nwv, 2),  # Alias for compatibility
            "confidence_level": round(confidence, 2),
            "method": method
        }
    
    def generate_cost_optimizations(self, company_id: str) -> List[Dict]:
        """Generate cost optimization recommendations"""
        optimizations = []
        
        # Get company
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            return []
        
        # Get recent transactions (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        transactions = self.db.query(WasteTransaction).filter(
            and_(
                WasteTransaction.company_id == company_id,
                WasteTransaction.transaction_date >= start_date
            )
        ).all()
        
        if not transactions:
            return []
        
        # 1. Segregation Quality Optimization
        avg_quality = statistics.mean([t.quality_score for t in transactions if t.quality_score])
        if avg_quality < 0.85:
            potential_savings = self._calculate_segregation_savings(transactions, avg_quality)
            if potential_savings > 0:
                optimizations.append({
                    "type": "segregation",
                    "current_cost": sum(t.disposal_cost for t in transactions),
                    "optimized_cost": sum(t.disposal_cost for t in transactions) - potential_savings,
                    "potential_savings": potential_savings,
                    "recommendation": f"Improve segregation quality from {avg_quality:.1%} to 90%+ to reduce contamination and increase recyclable revenue by ₹{potential_savings:,.0f}/month",
                    "implementation_difficulty": "medium",
                    "estimated_time": "2-4 weeks"
                })
        
        # 2. Volume-based Pricing Optimization
        volume_optimization = self._analyze_volume_pricing(transactions, company.location)
        if volume_optimization:
            optimizations.append(volume_optimization)
        
        # 3. Material Mix Optimization
        material_mix = self._analyze_material_mix(transactions)
        if material_mix:
            optimizations.append(material_mix)
        
        # Save optimizations
        for opt in optimizations:
            opt_record = CostOptimization(
                company_id=company_id,
                optimization_type=opt["type"],
                current_cost=opt["current_cost"],
                optimized_cost=opt["optimized_cost"],
                potential_savings=opt["potential_savings"],
                recommendation=opt["recommendation"],
                implementation_difficulty=opt.get("implementation_difficulty", "medium"),
                estimated_implementation_time=opt.get("estimated_time", "Unknown")
            )
            self.db.add(opt_record)
        
        self.db.commit()
        
        return optimizations
    
    def _calculate_segregation_savings(self, transactions: List[WasteTransaction], current_avg: float) -> float:
        """Calculate potential savings from improved segregation"""
        recyclable_txns = [t for t in transactions if t.material_category.value == "recyclable"]
        if not recyclable_txns:
            return 0.0
        
        current_revenue = sum(t.total_revenue for t in recyclable_txns)
        improved_quality = 0.90  # Target quality
        quality_improvement = improved_quality / current_avg if current_avg > 0 else 1.0
        
        potential_revenue = current_revenue * quality_improvement
        return potential_revenue - current_revenue
    
    def _analyze_volume_pricing(self, transactions: List[WasteTransaction], location: str) -> Optional[Dict]:
        """Analyze if volume-based pricing could save money"""
        # Group by material type
        material_volumes = {}
        for txn in transactions:
            if txn.material_type not in material_volumes:
                material_volumes[txn.material_type] = 0.0
            material_volumes[txn.material_type] += txn.quantity_kg
        
        # Check for volume pricing opportunities
        for material, total_volume in material_volumes.items():
            if total_volume < 1000:  # Less than 1 ton
                continue
            
            # Check if better volume pricing exists
            volume_price = self.db.query(MaterialPrice).filter(
                and_(
                    MaterialPrice.material_type == material,
                    MaterialPrice.location == location,
                    MaterialPrice.min_quantity_kg <= total_volume,
                    MaterialPrice.is_active == True
                )
            ).order_by(MaterialPrice.price_per_kg.desc()).first()
            
            if volume_price:
                current_revenue = sum(
                    t.total_revenue for t in transactions 
                    if t.material_type == material
                )
                potential_revenue = total_volume * volume_price.price_per_kg
                
                if potential_revenue > current_revenue:
                    return {
                        "type": "volume_pricing",
                        "current_cost": 0.0,
                        "optimized_cost": 0.0,
                        "potential_savings": potential_revenue - current_revenue,
                        "recommendation": f"Consolidate {material} collection to reach {volume_price.min_quantity_kg:.0f}kg minimum for better pricing. Potential increase: ₹{potential_revenue - current_revenue:,.0f}/month",
                        "implementation_difficulty": "low",
                        "estimated_time": "1-2 weeks"
                    }
        
        return None
    
    def _analyze_material_mix(self, transactions: List[WasteTransaction]) -> Optional[Dict]:
        """Analyze material mix for optimization opportunities"""
        # Find materials with low quality scores that could be improved
        low_quality_materials = {}
        
        for txn in transactions:
            if txn.quality_score and txn.quality_score < 0.7:
                if txn.material_type not in low_quality_materials:
                    low_quality_materials[txn.material_type] = {
                        "total_quantity": 0.0,
                        "avg_quality": [],
                        "total_revenue": 0.0
                    }
                
                low_quality_materials[txn.material_type]["total_quantity"] += txn.quantity_kg
                low_quality_materials[txn.material_type]["avg_quality"].append(txn.quality_score)
                low_quality_materials[txn.material_type]["total_revenue"] += txn.total_revenue
        
        if not low_quality_materials:
            return None
        
        # Find material with highest potential
        best_opportunity = None
        max_potential = 0.0
        
        for material, data in low_quality_materials.items():
            avg_quality = statistics.mean(data["avg_quality"])
            current_revenue = data["total_revenue"]
            potential_revenue = current_revenue * (0.85 / avg_quality)  # Improve to 85%
            potential = potential_revenue - current_revenue
            
            if potential > max_potential:
                max_potential = potential
                best_opportunity = {
                    "material": material,
                    "current_quality": avg_quality,
                    "potential_savings": potential
                }
        
        if best_opportunity:
            return {
                "type": "material_mix",
                "current_cost": 0.0,
                "optimized_cost": 0.0,
                "potential_savings": best_opportunity["potential_savings"],
                "recommendation": f"Focus on improving {best_opportunity['material']} quality from {best_opportunity['current_quality']:.1%} to 85%+. Potential revenue increase: ₹{best_opportunity['potential_savings']:,.0f}/month",
                "implementation_difficulty": "medium",
                "estimated_time": "3-4 weeks"
            }
        
        return None

