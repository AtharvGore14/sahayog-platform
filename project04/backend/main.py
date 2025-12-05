from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FASTAPI_ROOT_PATH = os.getenv("FASTAPI_ROOT_PATH", "")
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

from backend.database import SessionLocal, engine, Base
from backend.models import (
    Company, WasteData, MaterialPrice, DisposalCost, 
    WasteTransaction, CollectionPoint, SegregationAudit, RevenueEntry, CostEntry
)
from backend.waste_valuation import WasteValuationModule
from backend.waste_entry import WasteEntryService
from backend.analytics import AnalyticsEngine
from backend.pdf_generator import generate_pdf_report
from pydantic import BaseModel

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Automated Waste Financial Ledger API", root_path=FASTAPI_ROOT_PATH)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _render_frontend(page: str) -> HTMLResponse:
    page_path = FRONTEND_DIR / f"{page}.html"
    if not page_path.exists():
        raise HTTPException(status_code=404, detail="Page not found")
    return HTMLResponse(page_path.read_text(encoding="utf-8"))


@app.get("/", response_class=HTMLResponse)
def root_page():
    return _render_frontend("home")


@app.get("/home.html", response_class=HTMLResponse)
def home_page():
    return _render_frontend("home")


@app.get("/index.html", response_class=HTMLResponse)
def index_page():
    return _render_frontend("index")


@app.get("/waste_entry.html", response_class=HTMLResponse)
def waste_entry_page():
    return _render_frontend("waste_entry")


@app.get("/analytics.html", response_class=HTMLResponse)
def analytics_page():
    return _render_frontend("analytics")


@app.get("/companies.html", response_class=HTMLResponse)
def companies_page():
    return _render_frontend("companies")

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

# Legacy endpoint (for backward compatibility)
@app.get("/api/reports/generate")
def generate_financial_report_legacy(
    company_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Legacy endpoint - redirects to new format."""
    return generate_financial_report(company_id, start_date, end_date, False, db)

# New endpoint format matching requirements
@app.get("/api/v1/waste/financial-report/{company_id}")
def generate_financial_report(
    company_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    compare_historical: bool = False,
    db: Session = Depends(get_db)
):
    """
    Generate financial report for a company.
    
    Args:
        company_id: Company identifier
        start_date: Start date in YYYY-MM-DD format (optional, defaults to start of current month)
        end_date: End date in YYYY-MM-DD format (optional, defaults to today)
        compare_historical: Whether to include historical comparison (default: False)
    """
    try:
        # Parse dates - ensure end_date includes the full day
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            # Set to end of day to include all transactions on that date
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        else:
            end_dt = datetime.now()
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            # Set to start of day
            start_dt = start_dt.replace(hour=0, minute=0, second=0)
        else:
            # Default to start of current month
            start_dt = datetime(end_dt.year, end_dt.month, 1).replace(hour=0, minute=0, second=0)
        
        # Initialize valuation module
        valuation_module = WasteValuationModule(db)
        
        # Generate report
        report = valuation_module.generate_report(company_id, start_dt, end_dt, compare_historical)
        
        return JSONResponse(content=report)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@app.get("/api/v1/waste/financial-report/{company_id}/pdf")
def download_pdf_report(
    company_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Generate and download PDF report for a company.
    """
    try:
        # Parse dates
        if end_date:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_dt = datetime.now()
        
        if start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start_dt = datetime(end_dt.year, end_dt.month, 1)
        
        # Initialize valuation module
        valuation_module = WasteValuationModule(db)
        
        # Generate report data
        report_data = valuation_module.generate_report(company_id, start_dt, end_dt)
        
        # Generate PDF
        pdf_path = generate_pdf_report(report_data, company_id)
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"waste_financial_report_{company_id}_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}.pdf"
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating PDF: {str(e)}")

@app.get("/api/companies")
def list_companies(db: Session = Depends(get_db)):
    """List all companies."""
    companies = db.query(Company).all()
    return [{"id": c.id, "name": c.name, "location": c.location} for c in companies]

@app.get("/api/companies/{company_id}")
def get_company(company_id: str, db: Session = Depends(get_db)):
    """Get company details."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"id": company.id, "name": company.name, "location": company.location}

# Pydantic models for request validation
class WasteTransactionCreate(BaseModel):
    company_id: str
    material_type: str
    material_category: str
    quantity_kg: float
    collection_point_id: Optional[int] = None
    quality_score: Optional[float] = None
    grade: Optional[str] = None
    contamination_level: Optional[float] = None
    transaction_date: Optional[str] = None
    recorded_by: Optional[str] = None
    notes: Optional[str] = None

class BulkTransactionImport(BaseModel):
    transactions: List[WasteTransactionCreate]

class CompanyCreate(BaseModel):
    company_id: str
    name: str
    location: str
    industry_type: Optional[str] = None

class CollectionPointCreate(BaseModel):
    name: str
    location: str

class RevenueEntryCreate(BaseModel):
    transaction_id: int
    actual_revenue: float
    expected_revenue: Optional[float] = None  # Optional - defaults to transaction's calculated revenue
    payment_method: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None
    revenue_date: Optional[str] = None
    recorded_by: Optional[str] = None

class BulkRevenueEntryCreate(BaseModel):
    revenue_entries: List[RevenueEntryCreate]

class CostEntryCreate(BaseModel):
    transaction_id: int
    actual_cost: float
    expected_cost: Optional[float] = None
    disposal_cost: Optional[float] = None
    transportation_cost: Optional[float] = None
    processing_cost: Optional[float] = None
    other_costs: Optional[float] = None
    cost_type: Optional[str] = None
    vendor_name: Optional[str] = None
    invoice_number: Optional[str] = None
    payment_method: Optional[str] = None
    notes: Optional[str] = None
    cost_date: Optional[str] = None
    recorded_by: Optional[str] = None

class BulkCostEntryCreate(BaseModel):
    cost_entries: List[CostEntryCreate]

# Waste Entry Endpoints - REAL DATA PROCESSING
@app.post("/api/v1/waste/transactions")
def create_waste_transaction(
    transaction: WasteTransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a new waste transaction with real-time processing."""
    try:
        service = WasteEntryService(db)
        
        # Parse date if provided
        txn_date = None
        if transaction.transaction_date:
            try:
                # Try ISO format with T separator (from datetime-local input)
                if 'T' in transaction.transaction_date:
                    txn_date = datetime.strptime(transaction.transaction_date, "%Y-%m-%dT%H:%M")
                # Try space separator format
                elif ' ' in transaction.transaction_date:
                    try:
                        txn_date = datetime.strptime(transaction.transaction_date, "%Y-%m-%d %H:%M:%S")
                    except:
                        txn_date = datetime.strptime(transaction.transaction_date, "%Y-%m-%d %H:%M")
                # Try date only
                else:
                    txn_date = datetime.strptime(transaction.transaction_date, "%Y-%m-%d")
            except Exception as e:
                raise ValueError(f"Invalid date format: {transaction.transaction_date}. Error: {str(e)}")
        
        result = service.create_waste_transaction(
            company_id=transaction.company_id,
            material_type=transaction.material_type,
            material_category=transaction.material_category,
            quantity_kg=transaction.quantity_kg,
            collection_point_id=transaction.collection_point_id,
            quality_score=transaction.quality_score,
            grade=transaction.grade,
            contamination_level=transaction.contamination_level,
            transaction_date=txn_date,
            recorded_by=transaction.recorded_by,
            notes=transaction.notes
        )
        
        return JSONResponse(content=result)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating transaction: {str(e)}")

@app.post("/api/v1/waste/transactions/bulk")
def bulk_import_transactions(
    bulk_data: BulkTransactionImport,
    db: Session = Depends(get_db)
):
    """Bulk import waste transactions."""
    try:
        service = WasteEntryService(db)
        
        transactions_data = []
        for txn in bulk_data.transactions:
            txn_dict = txn.dict()
            # Parse date if provided
            if txn_dict.get("transaction_date"):
                date_str = txn_dict["transaction_date"]
                try:
                    # Try ISO format with T separator (from datetime-local input)
                    if 'T' in date_str:
                        txn_dict["transaction_date"] = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
                    # Try space separator format
                    elif ' ' in date_str:
                        try:
                            txn_dict["transaction_date"] = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            txn_dict["transaction_date"] = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                    # Try date only
                    else:
                        txn_dict["transaction_date"] = datetime.strptime(date_str, "%Y-%m-%d")
                except Exception:
                    # If parsing fails, remove the date field and let backend use current time
                    del txn_dict["transaction_date"]
            transactions_data.append(txn_dict)
        
        result = service.bulk_import_transactions(transactions_data)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing transactions: {str(e)}")

@app.get("/api/v1/waste/transactions")
def get_waste_transactions(
    company_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    collection_point_id: Optional[int] = None,
    material_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get waste transactions with filters."""
    try:
        service = WasteEntryService(db)
        
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        
        transactions = service.get_transactions(
            company_id=company_id,
            start_date=start_dt,
            end_date=end_dt,
            collection_point_id=collection_point_id,
            material_type=material_type
        )
        
        return JSONResponse(content={"transactions": transactions, "count": len(transactions)})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")

# Collection Points Management
@app.post("/api/v1/companies")
def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db)
):
    """Create a new company."""
    # Check if company already exists
    existing = db.query(Company).filter(Company.id == company_data.company_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Company {company_data.company_id} already exists")
    
    company = Company(
        id=company_data.company_id,
        name=company_data.name,
        location=company_data.location,
        industry_type=company_data.industry_type
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    
    return {"id": company.id, "name": company.name, "location": company.location}

@app.post("/api/v1/companies/{company_id}/collection-points")
def create_collection_point(
    company_id: str,
    point_data: CollectionPointCreate,
    db: Session = Depends(get_db)
):
    """Create a new collection point."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    cp = CollectionPoint(
        company_id=company_id,
        name=point_data.name,
        location=point_data.location
    )
    db.add(cp)
    db.commit()
    db.refresh(cp)
    
    return {"id": cp.id, "name": cp.name, "location": cp.location, "company_id": company_id}

@app.get("/api/v1/companies/{company_id}/collection-points")
def list_collection_points(company_id: str, db: Session = Depends(get_db)):
    """List all collection points for a company."""
    # First check if company exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found")
    
    points = db.query(CollectionPoint).filter(
        CollectionPoint.company_id == company_id,
        CollectionPoint.is_active == True
    ).all()
    
    return [{"id": p.id, "name": p.name, "location": p.location} for p in points]

# Analytics Endpoints
@app.get("/api/v1/waste/analytics/trends/{company_id}")
def get_trends(
    company_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get waste financial trends."""
    try:
        engine = AnalyticsEngine(db)
        trends = engine.calculate_trends(company_id, days)
        return JSONResponse(content=trends)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating trends: {str(e)}")

@app.get("/api/v1/waste/analytics/forecast/{company_id}")
def get_forecast(
    company_id: str,
    days: int = 30,
    method: str = "moving_average",
    db: Session = Depends(get_db)
):
    """Get NWV forecast."""
    try:
        engine = AnalyticsEngine(db)
        forecast = engine.forecast_nwv(company_id, days, method)
        return JSONResponse(content=forecast)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

@app.get("/api/v1/waste/analytics/optimizations/{company_id}")
def get_optimizations(
    company_id: str,
    db: Session = Depends(get_db)
):
    """Get cost optimization recommendations."""
    try:
        engine = AnalyticsEngine(db)
        optimizations = engine.generate_cost_optimizations(company_id)
        
        # Extract recommendations as strings for easier frontend consumption
        recommendations = [opt.get("recommendation", str(opt)) for opt in optimizations] if optimizations else []
        
        return JSONResponse(content={
            "optimizations": optimizations,
            "recommendations": recommendations,  # Also include as simple string array
            "count": len(optimizations)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating optimizations: {str(e)}")

# Segregation Audit Endpoints
@app.post("/api/v1/waste/audits")
def create_segregation_audit(
    company_id: str,
    collection_point_id: Optional[int] = None,
    segregation_quality_score: float = 1.0,
    contamination_percentage: float = 0.0,
    proper_labeling_score: float = 1.0,
    compliance_score: float = 1.0,
    issues_found: Optional[str] = None,
    recommendations: Optional[str] = None,
    auditor_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a segregation audit."""
    audit = SegregationAudit(
        company_id=company_id,
        collection_point_id=collection_point_id,
        segregation_quality_score=segregation_quality_score,
        contamination_percentage=contamination_percentage,
        proper_labeling_score=proper_labeling_score,
        compliance_score=compliance_score,
        issues_found=issues_found,
        recommendations=recommendations,
        auditor_name=auditor_name
    )
    
    db.add(audit)
    db.commit()
    db.refresh(audit)
    
    return {
        "id": audit.id,
        "company_id": company_id,
        "audit_date": audit.audit_date.isoformat(),
        "segregation_quality_score": audit.segregation_quality_score
    }

# Revenue Entry Endpoints
@app.post("/api/v1/revenue/entries")
def create_revenue_entry(
    revenue_data: RevenueEntryCreate,
    db: Session = Depends(get_db)
):
    """Create a revenue entry for a transaction."""
    try:
        # Get transaction
        transaction = db.query(WasteTransaction).filter(
            WasteTransaction.id == revenue_data.transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Parse revenue date
        revenue_date = datetime.utcnow()
        if revenue_data.revenue_date:
            try:
                if 'T' in revenue_data.revenue_date:
                    revenue_date = datetime.strptime(revenue_data.revenue_date, "%Y-%m-%dT%H:%M")
                elif ' ' in revenue_data.revenue_date:
                    try:
                        revenue_date = datetime.strptime(revenue_data.revenue_date, "%Y-%m-%d %H:%M:%S")
                    except:
                        revenue_date = datetime.strptime(revenue_data.revenue_date, "%Y-%m-%d %H:%M")
                else:
                    revenue_date = datetime.strptime(revenue_data.revenue_date, "%Y-%m-%d")
            except Exception as e:
                raise ValueError(f"Invalid date format: {revenue_data.revenue_date}")
        
        # Calculate variance - use provided expected_revenue or fall back to transaction's calculated revenue
        expected_revenue = revenue_data.expected_revenue if revenue_data.expected_revenue is not None else (transaction.total_revenue or 0.0)
        revenue_variance = revenue_data.actual_revenue - expected_revenue
        
        # Create revenue entry
        revenue_entry = RevenueEntry(
            transaction_id=revenue_data.transaction_id,
            company_id=transaction.company_id,
            actual_revenue=revenue_data.actual_revenue,
            expected_revenue=expected_revenue,
            revenue_variance=revenue_variance,
            revenue_date=revenue_date,
            payment_method=revenue_data.payment_method,
            vendor_name=revenue_data.vendor_name,
            invoice_number=revenue_data.invoice_number,
            notes=revenue_data.notes,
            recorded_by=revenue_data.recorded_by
        )
        
        db.add(revenue_entry)
        db.commit()
        db.refresh(revenue_entry)
        
        return {
            "id": revenue_entry.id,
            "transaction_id": revenue_entry.transaction_id,
            "actual_revenue": revenue_entry.actual_revenue,
            "expected_revenue": revenue_entry.expected_revenue,
            "revenue_variance": revenue_entry.revenue_variance,
            "revenue_date": revenue_entry.revenue_date.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating revenue entry: {str(e)}")

@app.post("/api/v1/revenue/entries/bulk")
def bulk_create_revenue_entries(
    bulk_data: BulkRevenueEntryCreate,
    db: Session = Depends(get_db)
):
    """Bulk create revenue entries."""
    results = {
        "successful": [],
        "failed": [],
        "total_count": len(bulk_data.revenue_entries)
    }
    
    for entry_data in bulk_data.revenue_entries:
        try:
            result = create_revenue_entry(entry_data, db)
            results["successful"].append(result)
        except Exception as e:
            results["failed"].append({
                "data": entry_data.dict(),
                "error": str(e)
            })
    
    return results

@app.get("/api/v1/revenue/entries")
def get_revenue_entries(
    company_id: str,
    transaction_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get revenue entries with filters."""
    query = db.query(RevenueEntry).filter(
        RevenueEntry.company_id == company_id
    )
    
    if transaction_id:
        query = query.filter(RevenueEntry.transaction_id == transaction_id)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(RevenueEntry.revenue_date >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(RevenueEntry.revenue_date <= end_dt)
    
    entries = query.order_by(RevenueEntry.revenue_date.desc()).all()
    
    return [
        {
            "id": e.id,
            "transaction_id": e.transaction_id,
            "actual_revenue": e.actual_revenue,
            "expected_revenue": e.expected_revenue,
            "revenue_variance": e.revenue_variance,
            "revenue_date": e.revenue_date.isoformat(),
            "payment_method": e.payment_method,
            "vendor_name": e.vendor_name,
            "invoice_number": e.invoice_number,
            "status": e.status,
            "transaction": {
                "material_type": e.transaction.material_type,
                "quantity_kg": e.transaction.quantity_kg,
                "transaction_date": e.transaction.transaction_date.isoformat()
            } if e.transaction else None
        }
        for e in entries
    ]

@app.get("/api/v1/revenue/analytics/{company_id}")
def get_revenue_analytics(
    company_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive revenue analytics."""
    from backend.analytics import AnalyticsEngine
    
    # Parse dates
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_dt = datetime.utcnow()
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = end_dt - timedelta(days=30)
    
    # Get transactions
    transactions = db.query(WasteTransaction).filter(
        and_(
            WasteTransaction.company_id == company_id,
            WasteTransaction.transaction_date >= start_dt,
            WasteTransaction.transaction_date <= end_dt
        )
    ).all()
    
    # Get revenue entries - check both revenue_date and transaction date range
    # First get transaction IDs in the date range
    transaction_ids_in_range = [t.id for t in transactions]
    
    # Build query for revenue entries
    revenue_query = db.query(RevenueEntry).filter(
        RevenueEntry.company_id == company_id
    )
    
    # Build OR conditions - include entries where:
    # 1. revenue_date is in the date range, OR
    # 2. transaction_id matches transactions in the date range
    conditions = []
    
    # Condition 1: revenue_date in range
    conditions.append(
        and_(
            RevenueEntry.revenue_date >= start_dt,
            RevenueEntry.revenue_date <= end_dt
        )
    )
    
    # Condition 2: transaction_id in range (if we have transactions)
    if transaction_ids_in_range:
        conditions.append(
            RevenueEntry.transaction_id.in_(transaction_ids_in_range)
        )
    
    # Apply OR filter if we have conditions
    if conditions:
        if len(conditions) > 1:
            revenue_query = revenue_query.filter(or_(*conditions))
        else:
            revenue_query = revenue_query.filter(conditions[0])
    
    revenue_entries = revenue_query.all()
    
    print(f"[Revenue Analytics] Found {len(revenue_entries)} revenue entries for company {company_id}")
    print(f"[Revenue Analytics] Date range: {start_dt} to {end_dt}")
    print(f"[Revenue Analytics] Transaction IDs in range: {len(transaction_ids_in_range)}")
    
    # Calculate metrics
    total_expected_revenue = sum(t.total_revenue or 0.0 for t in transactions)
    total_actual_revenue = sum(e.actual_revenue for e in revenue_entries)
    total_variance = sum(e.revenue_variance for e in revenue_entries)
    
    # Material-wise analysis
    material_analysis = {}
    for entry in revenue_entries:
        mat_type = entry.transaction.material_type if entry.transaction else "Unknown"
        if mat_type not in material_analysis:
            material_analysis[mat_type] = {
                "expected": 0.0,
                "actual": 0.0,
                "variance": 0.0,
                "count": 0
            }
        material_analysis[mat_type]["expected"] += entry.expected_revenue
        material_analysis[mat_type]["actual"] += entry.actual_revenue
        material_analysis[mat_type]["variance"] += entry.revenue_variance
        material_analysis[mat_type]["count"] += 1
    
    # Vendor analysis
    vendor_analysis = {}
    for entry in revenue_entries:
        vendor = entry.vendor_name or "Unknown"
        if vendor not in vendor_analysis:
            vendor_analysis[vendor] = {
                "total_revenue": 0.0,
                "transaction_count": 0
            }
        vendor_analysis[vendor]["total_revenue"] += entry.actual_revenue
        vendor_analysis[vendor]["transaction_count"] += 1
    
    # Payment method analysis
    payment_analysis = {}
    for entry in revenue_entries:
        method = entry.payment_method or "Unknown"
        if method not in payment_analysis:
            payment_analysis[method] = {
                "total_revenue": 0.0,
                "count": 0
            }
        payment_analysis[method]["total_revenue"] += entry.actual_revenue
        payment_analysis[method]["count"] += 1
    
    # Variance analysis
    positive_variances = [e for e in revenue_entries if e.revenue_variance > 0]
    negative_variances = [e for e in revenue_entries if e.revenue_variance < 0]
    
    return {
        "period": {
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat()
        },
        "summary": {
            "total_expected_revenue": round(total_expected_revenue, 2),
            "total_actual_revenue": round(total_actual_revenue, 2),
            "total_variance": round(total_variance, 2),
            "variance_percentage": round((total_variance / total_expected_revenue * 100) if total_expected_revenue > 0 else 0, 2),
            "revenue_entries_count": len(revenue_entries),
            "transactions_without_revenue": len(transactions) - len(revenue_entries)
        },
        "material_analysis": {
            mat: {
                "expected_revenue": round(data["expected"], 2),
                "actual_revenue": round(data["actual"], 2),
                "variance": round(data["variance"], 2),
                "variance_percentage": round((data["variance"] / data["expected"] * 100) if data["expected"] > 0 else 0, 2),
                "entry_count": data["count"]
            }
            for mat, data in material_analysis.items()
        },
        "vendor_analysis": {
            vendor: {
                "total_revenue": round(data["total_revenue"], 2),
                "transaction_count": data["transaction_count"],
                "avg_revenue_per_transaction": round(data["total_revenue"] / data["transaction_count"], 2) if data["transaction_count"] > 0 else 0
            }
            for vendor, data in vendor_analysis.items()
        },
        "payment_method_analysis": {
            method: {
                "total_revenue": round(data["total_revenue"], 2),
                "count": data["count"],
                "percentage": round((data["total_revenue"] / total_actual_revenue * 100) if total_actual_revenue > 0 else 0, 2)
            }
            for method, data in payment_analysis.items()
        },
        "variance_analysis": {
            "positive_variances": len(positive_variances),
            "negative_variances": len(negative_variances),
            "total_positive_variance": round(sum(e.revenue_variance for e in positive_variances), 2),
            "total_negative_variance": round(sum(e.revenue_variance for e in negative_variances), 2),
            "average_variance": round(total_variance / len(revenue_entries) if revenue_entries else 0, 2)
        }
    }
    
    print(f"[Revenue Analytics] Returning result with {len(revenue_entries)} entries")
    return result

# Cost Entry Endpoints
@app.post("/api/v1/cost/entries")
def create_cost_entry(
    cost_data: CostEntryCreate,
    db: Session = Depends(get_db)
):
    """Create a cost entry for a transaction."""
    try:
        # Get transaction
        transaction = db.query(WasteTransaction).filter(
            WasteTransaction.id == cost_data.transaction_id
        ).first()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Parse cost date
        cost_date = datetime.utcnow()
        if cost_data.cost_date:
            try:
                if 'T' in cost_data.cost_date:
                    cost_date = datetime.strptime(cost_data.cost_date, "%Y-%m-%dT%H:%M")
                elif ' ' in cost_data.cost_date:
                    try:
                        cost_date = datetime.strptime(cost_data.cost_date, "%Y-%m-%d %H:%M:%S")
                    except:
                        cost_date = datetime.strptime(cost_data.cost_date, "%Y-%m-%d %H:%M")
                else:
                    cost_date = datetime.strptime(cost_data.cost_date, "%Y-%m-%d")
            except Exception as e:
                raise ValueError(f"Invalid date format: {cost_data.cost_date}")
        
        # Calculate variance
        expected_cost = cost_data.expected_cost if cost_data.expected_cost is not None else (transaction.disposal_cost or 0.0)
        
        # Calculate total cost from breakdown if provided
        total_breakdown = sum([
            cost_data.disposal_cost or 0.0,
            cost_data.transportation_cost or 0.0,
            cost_data.processing_cost or 0.0,
            cost_data.other_costs or 0.0
        ])
        
        # If breakdown provided, use it; otherwise use actual_cost
        if total_breakdown > 0:
            actual_cost = total_breakdown
        else:
            actual_cost = cost_data.actual_cost
        
        cost_variance = actual_cost - expected_cost
        
        # Create cost entry
        cost_entry = CostEntry(
            transaction_id=cost_data.transaction_id,
            company_id=transaction.company_id,
            actual_cost=actual_cost,
            expected_cost=expected_cost,
            cost_variance=cost_variance,
            disposal_cost=cost_data.disposal_cost,
            transportation_cost=cost_data.transportation_cost,
            processing_cost=cost_data.processing_cost,
            other_costs=cost_data.other_costs,
            cost_date=cost_date,
            cost_type=cost_data.cost_type,
            vendor_name=cost_data.vendor_name,
            invoice_number=cost_data.invoice_number,
            payment_method=cost_data.payment_method,
            notes=cost_data.notes,
            recorded_by=cost_data.recorded_by
        )
        
        db.add(cost_entry)
        db.commit()
        db.refresh(cost_entry)
        
        return {
            "id": cost_entry.id,
            "transaction_id": cost_entry.transaction_id,
            "actual_cost": cost_entry.actual_cost,
            "expected_cost": cost_entry.expected_cost,
            "cost_variance": cost_entry.cost_variance,
            "cost_date": cost_entry.cost_date.isoformat()
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating cost entry: {str(e)}")

@app.post("/api/v1/cost/entries/bulk")
def bulk_create_cost_entries(
    bulk_data: BulkCostEntryCreate,
    db: Session = Depends(get_db)
):
    """Bulk create cost entries."""
    results = {
        "successful": [],
        "failed": [],
        "total_count": len(bulk_data.cost_entries)
    }
    
    for entry_data in bulk_data.cost_entries:
        try:
            result = create_cost_entry(entry_data, db)
            results["successful"].append(result)
        except Exception as e:
            results["failed"].append({
                "data": entry_data.dict(),
                "error": str(e)
            })
    
    return results

@app.get("/api/v1/cost/entries")
def get_cost_entries(
    company_id: str,
    transaction_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get cost entries with filters."""
    query = db.query(CostEntry).filter(
        CostEntry.company_id == company_id
    )
    
    if transaction_id:
        query = query.filter(CostEntry.transaction_id == transaction_id)
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(CostEntry.cost_date >= start_dt)
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt = end_dt.replace(hour=23, minute=59, second=59)
        query = query.filter(CostEntry.cost_date <= end_dt)
    
    entries = query.order_by(CostEntry.cost_date.desc()).all()
    
    return [
        {
            "id": e.id,
            "transaction_id": e.transaction_id,
            "actual_cost": e.actual_cost,
            "expected_cost": e.expected_cost,
            "cost_variance": e.cost_variance,
            "disposal_cost": e.disposal_cost,
            "transportation_cost": e.transportation_cost,
            "processing_cost": e.processing_cost,
            "other_costs": e.other_costs,
            "cost_date": e.cost_date.isoformat(),
            "cost_type": e.cost_type,
            "vendor_name": e.vendor_name,
            "invoice_number": e.invoice_number,
            "status": e.status,
            "transaction": {
                "material_type": e.transaction.material_type,
                "quantity_kg": e.transaction.quantity_kg,
                "transaction_date": e.transaction.transaction_date.isoformat()
            } if e.transaction else None
        }
        for e in entries
    ]

@app.get("/api/v1/cost/analytics/{company_id}")
def get_cost_analytics(
    company_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get comprehensive cost analytics."""
    # Parse dates
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_dt = datetime.utcnow()
    
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = end_dt - timedelta(days=30)
    
    # Get transactions
    transactions = db.query(WasteTransaction).filter(
        and_(
            WasteTransaction.company_id == company_id,
            WasteTransaction.transaction_date >= start_dt,
            WasteTransaction.transaction_date <= end_dt
        )
    ).all()
    
    # Get cost entries
    cost_entries = db.query(CostEntry).filter(
        and_(
            CostEntry.company_id == company_id,
            CostEntry.cost_date >= start_dt,
            CostEntry.cost_date <= end_dt
        )
    ).all()
    
    # Calculate metrics
    total_expected_cost = sum(t.disposal_cost or 0.0 for t in transactions)
    total_actual_cost = sum(e.actual_cost for e in cost_entries)
    total_variance = sum(e.cost_variance for e in cost_entries)
    
    # Cost breakdown analysis
    cost_breakdown = {
        "disposal": sum(e.disposal_cost or 0.0 for e in cost_entries),
        "transportation": sum(e.transportation_cost or 0.0 for e in cost_entries),
        "processing": sum(e.processing_cost or 0.0 for e in cost_entries),
        "other": sum(e.other_costs or 0.0 for e in cost_entries)
    }
    
    # Material-wise analysis
    material_analysis = {}
    for entry in cost_entries:
        mat_type = entry.transaction.material_type if entry.transaction else "Unknown"
        if mat_type not in material_analysis:
            material_analysis[mat_type] = {
                "expected": 0.0,
                "actual": 0.0,
                "variance": 0.0,
                "count": 0
            }
        material_analysis[mat_type]["expected"] += entry.expected_cost
        material_analysis[mat_type]["actual"] += entry.actual_cost
        material_analysis[mat_type]["variance"] += entry.cost_variance
        material_analysis[mat_type]["count"] += 1
    
    # Vendor analysis
    vendor_analysis = {}
    for entry in cost_entries:
        vendor = entry.vendor_name or "Unknown"
        if vendor not in vendor_analysis:
            vendor_analysis[vendor] = {
                "total_cost": 0.0,
                "transaction_count": 0
            }
        vendor_analysis[vendor]["total_cost"] += entry.actual_cost
        vendor_analysis[vendor]["transaction_count"] += 1
    
    # Cost type analysis
    cost_type_analysis = {}
    for entry in cost_entries:
        cost_type = entry.cost_type or "Unknown"
        if cost_type not in cost_type_analysis:
            cost_type_analysis[cost_type] = {
                "total_cost": 0.0,
                "count": 0
            }
        cost_type_analysis[cost_type]["total_cost"] += entry.actual_cost
        cost_type_analysis[cost_type]["count"] += 1
    
    # Variance analysis
    positive_variances = [e for e in cost_entries if e.cost_variance > 0]
    negative_variances = [e for e in cost_entries if e.cost_variance < 0]
    
    return {
        "period": {
            "start_date": start_dt.isoformat(),
            "end_date": end_dt.isoformat()
        },
        "summary": {
            "total_expected_cost": round(total_expected_cost, 2),
            "total_actual_cost": round(total_actual_cost, 2),
            "total_variance": round(total_variance, 2),
            "variance_percentage": round((total_variance / total_expected_cost * 100) if total_expected_cost > 0 else 0, 2),
            "cost_entries_count": len(cost_entries),
            "transactions_without_cost": len(transactions) - len(cost_entries)
        },
        "cost_breakdown": {
            "disposal": round(cost_breakdown["disposal"], 2),
            "transportation": round(cost_breakdown["transportation"], 2),
            "processing": round(cost_breakdown["processing"], 2),
            "other": round(cost_breakdown["other"], 2),
            "total": round(sum(cost_breakdown.values()), 2)
        },
        "material_analysis": {
            mat: {
                "expected_cost": round(data["expected"], 2),
                "actual_cost": round(data["actual"], 2),
                "variance": round(data["variance"], 2),
                "variance_percentage": round((data["variance"] / data["expected"] * 100) if data["expected"] > 0 else 0, 2),
                "entry_count": data["count"]
            }
            for mat, data in material_analysis.items()
        },
        "vendor_analysis": {
            vendor: {
                "total_cost": round(data["total_cost"], 2),
                "transaction_count": data["transaction_count"],
                "avg_cost_per_transaction": round(data["total_cost"] / data["transaction_count"], 2) if data["transaction_count"] > 0 else 0
            }
            for vendor, data in vendor_analysis.items()
        },
        "cost_type_analysis": {
            cost_type: {
                "total_cost": round(data["total_cost"], 2),
                "count": data["count"],
                "percentage": round((data["total_cost"] / total_actual_cost * 100) if total_actual_cost > 0 else 0, 2)
            }
            for cost_type, data in cost_type_analysis.items()
        },
        "variance_analysis": {
            "positive_variances": len(positive_variances),
            "negative_variances": len(negative_variances),
            "total_positive_variance": round(sum(e.cost_variance for e in positive_variances), 2),
            "total_negative_variance": round(sum(e.cost_variance for e in negative_variances), 2),
            "average_variance": round(total_variance / len(cost_entries) if cost_entries else 0, 2)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

