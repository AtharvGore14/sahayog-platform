from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./waste_ledger.db')

# Convert Render PostgreSQL URL to SQLAlchemy format if needed
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

# Create engine based on database type
if DATABASE_URL.startswith('postgresql://'):
    # PostgreSQL connection
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # SQLite connection (for local development)
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

