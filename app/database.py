# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# You can also use environment variables here if you want (recommended)
DATABASE_URL = "mysql+pymysql://root:@localhost/myfile"


# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # checks connection health before using it
)

# Create a configured "Session" class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for models to inherit from
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Dependency function to get DB session (for FastAPI Depends)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
