# ♻️ Automated Waste Financial Ledger

A comprehensive financial intelligence platform that transforms waste data into actionable financial insights, calculating Net Waste Value (NWV) for businesses.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python setup.py
```

### 3. Start Backend Server
```bash
python run_server.py
```
Or use the convenient scripts:
- **Windows:** Double-click `START_BACKEND.bat`
- **Linux/Mac:** Run `./START_BACKEND.sh`

### 4. Open the Application
Open `frontend/home.html` in your web browser or serve it:
```bash
# Using Python
python -m http.server 8080
# Then navigate to http://localhost:8080/frontend/home.html
```

## 📋 Features

### ✨ Core Features
- **Financial Dashboard** - Real-time financial reports with comprehensive analytics
- **Data Entry** - Easy-to-use forms for waste transaction entry
- **Advanced Analytics** - Predictive analytics, trends, and forecasting
- **Company Management** - Manage multiple companies and collection points
- **PDF Reports** - Download comprehensive financial reports
- **Material Tracking** - Track all recyclable and non-recyclable materials
- **Collection Points** - Track waste by location within companies
- **Quality Scoring** - Integrate segregation audit quality scores

### 📊 Dashboard Features
- Net Waste Value (NWV) calculation
- Revenue breakdown by material
- Cost breakdown by category
- Daily trends visualization
- Transaction details table
- Material-wise summary
- Category-wise summary
- Historical comparison
- Strategic recommendations

### 📝 Data Entry Features
- Real-time transaction entry
- Automatic price/cost calculation
- Collection point selection
- Quality score integration
- Company creation on-the-fly
- Collection point creation

### 📈 Analytics Features
- Trend analysis (improving/declining)
- NWV forecasting
- Cost optimization recommendations
- Daily trend charts
- Predictive insights

## 🏗️ Architecture

### Backend (FastAPI)
- RESTful API endpoints
- SQLite database
- Real-time calculations
- PDF report generation
- Advanced analytics engine

### Frontend (HTML/CSS/JavaScript)
- Modern, responsive design
- Chart.js visualizations
- Unified navigation
- Real-time updates

## 📁 Project Structure

```
Feature5/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # Database models
│   ├── waste_valuation.py  # Core NWV calculation
│   ├── waste_entry.py       # Transaction processing
│   ├── analytics.py         # Analytics engine
│   └── pdf_generator.py     # PDF report generation
├── frontend/
│   ├── home.html            # Landing page
│   ├── index.html           # Financial dashboard
│   ├── waste_entry.html     # Data entry form
│   ├── analytics.html       # Analytics dashboard
│   └── companies.html       # Company management
├── requirements.txt         # Python dependencies
├── setup.py                 # Database initialization
└── run_server.py            # Server startup script
```

## 🔗 Navigation

The application includes unified navigation across all pages:
- **Home** - Landing page with feature overview
- **Dashboard** - Financial reports and analytics
- **Data Entry** - Enter waste transactions
- **Analytics** - Advanced insights and forecasting
- **Companies** - Manage companies and collection points

## 📚 API Endpoints

### Financial Reports
- `GET /api/v1/waste/financial-report/{company_id}` - Generate financial report
- `GET /api/v1/waste/financial-report/{company_id}/pdf` - Download PDF report

### Transactions
- `POST /api/v1/waste/transactions` - Create transaction
- `GET /api/v1/waste/transactions` - List transactions

### Companies
- `POST /api/v1/companies` - Create company
- `GET /api/companies` - List all companies
- `POST /api/v1/companies/{id}/collection-points` - Create collection point
- `GET /api/v1/companies/{id}/collection-points` - List collection points

### Analytics
- `GET /api/v1/waste/analytics/trends/{company_id}` - Get trends
- `GET /api/v1/waste/analytics/forecast/{company_id}` - Get forecast
- `GET /api/v1/waste/analytics/optimizations/{company_id}` - Get optimizations

## 🛠️ Utilities

- `setup.py` - Initialize database and seed sample data
- `START_BACKEND.bat` / `START_BACKEND.sh` - Start server scripts
- `QUICK_RESET.bat` - Quick database reset
- `FORCE_RESET.bat` - Force database reset (kills processes)

## 💡 Real-World Features

This system implements real-world waste management practices:
- **Market-based pricing** - Real-time material prices
- **Quality-adjusted pricing** - Better quality = better price
- **Location-based costs** - Different disposal costs by location
- **Collection point tracking** - Track waste by physical location
- **Segregation audits** - Quality scoring and compliance
- **Forecasting** - Predict future NWV using statistical methods
- **Cost optimization** - Algorithm-based recommendations

## 📞 Support

For issues or questions, check the console output or ensure the backend server is running on `http://localhost:8000`.
