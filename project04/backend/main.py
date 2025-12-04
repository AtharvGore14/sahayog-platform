from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from sqlalchemy.orm import Session
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
    WasteTransaction, CollectionPoint, SegregationAudit
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

