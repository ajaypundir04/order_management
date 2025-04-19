from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
import os
from typing import Generator

# Database configuration from environment variables (or defaults)
db_host = os.environ.get("DB_HOST", "localhost")
db_user = os.environ.get("DB_USER", "root")
db_password = os.environ.get("DB_PASSWORD", "password")
db_name = os.environ.get("DB_NAME", "lemon_markets")

# Construct the SQLAlchemy database URL.
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=5, max_overflow=10)
# Use scoped_session to ensure thread safety
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def get_db() -> Generator[Session, None, None]:
    """
    Get a database session.  This function uses a scoped session, which is
    thread-safe.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        SessionLocal.remove()