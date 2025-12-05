# Sahayog Platform - Integrated Sustainability Suite

A comprehensive multi-application platform for waste management, route optimization, auditing, marketplace, and financial ledger management.

## 🚀 Applications

1. **Route Optimizer** (`/django`) - AI-powered route optimization for waste collection
2. **Auditing System** (`/auditing`) - Waste auditing and analysis with AI
3. **Marketplace** (`/marketplace`) - AI-enhanced circular economy marketplace
4. **Waste Ledger** (`/ledger`) - Automated financial ledger for waste transactions

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL (for production)
- Redis (for Celery and WebSockets)
- Git

## 🛠️ Local Development Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd CP_4dec
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the root directory (optional for local dev):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///./db.sqlite3  # Optional, defaults to SQLite
REDIS_URL=redis://localhost:6379/0  # Optional, defaults to localhost
```

### 5. Run Migrations

```bash
# For Route Optimizer
cd project01_route_opt
python manage.py migrate
cd ..

# For Marketplace
cd project03_market_place
python manage.py migrate
cd ..
```

### 6. Create Superusers (Optional)

```bash
# Route Optimizer
cd project01_route_opt
python manage.py createsuperuser
cd ..

# Marketplace
cd project03_market_place
python manage.py createsuperuser
cd ..
```

### 7. Start the Server

```bash
python master_server.py
```

The application will be available at `http://localhost:8000`

## 🌐 Production Deployment

This project is configured for deployment on Render. See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed instructions.

### Quick Deploy to Render

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Blueprint"
4. Connect your repository
5. Render will auto-detect `render.yaml` and create all services

For detailed instructions, see [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md)

## 📁 Project Structure

```
CP_4dec/
├── master_server.py          # Main WSGI server
├── requirements.txt           # Python dependencies
├── render.yaml               # Render deployment config
├── Procfile                  # Process definitions
├── build.sh                  # Build script
├── project01_route_opt/      # Route Optimizer (Django)
├── project02_auditing/       # Auditing System (Flask)
├── project03_market_place/   # Marketplace (Django + Channels)
└── project04/                # Waste Ledger (FastAPI)
```

## 🔧 Configuration

### Database

- **Development**: Uses SQLite (default)
- **Production**: Uses PostgreSQL (via `DATABASE_URL` environment variable)

### Redis

- **Development**: Uses local Redis (default: `redis://localhost:6379/0`)
- **Production**: Uses Redis from `REDIS_URL` environment variable

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generated/required |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Allowed hosts | `*` |
| `DATABASE_URL` | Database connection string | SQLite |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `DJANGO_SETTINGS_MODULE` | Django settings module | `sahayog.settings` |
| `FASTAPI_ROOT_PATH` | FastAPI root path | `/ledger` |

## 🧪 Testing

```bash
# Run Django tests
cd project01_route_opt
python manage.py test
cd ..

cd project03_market_place
python manage.py test
cd ..
```

## 📝 API Documentation

- Route Optimizer API: `/django/api/`
- Marketplace API: `/marketplace/api/`
- Waste Ledger API: `/ledger/api/docs` (FastAPI Swagger)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is part of the Sahayog Platform.

## 🆘 Support

For deployment issues, see:
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) - Full deployment guide
- [QUICK_START_RENDER.md](QUICK_START_RENDER.md) - Quick deployment reference
- [DATABASE_CONFIG_EXAMPLES.md](DATABASE_CONFIG_EXAMPLES.md) - Database configuration examples

## 🔒 Security

- Never commit `.env` files
- Use strong `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` properly
- Use HTTPS in production (automatic on Render)

---

**Built with ❤️ for sustainable waste management**

