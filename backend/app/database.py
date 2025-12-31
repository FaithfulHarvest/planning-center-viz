"""Database connection and session management."""
import logging
import time
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import DBAPIError, OperationalError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Create engine with Azure SQL Server specific settings
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,  # Recycle connections every 5 minutes
    connect_args={
        "timeout": 60,
        "TrustServerCertificate": "yes",
    }
)


def _connect_with_retry(dialect, conn_rec, cargs, cparams):
    """
    Custom connection function with retry logic for Azure SQL cold start.
    Azure SQL Serverless pauses after inactivity and can take 10-60 seconds to wake up.
    """
    max_retries = 5
    retry_delay = 3  # seconds

    for attempt in range(max_retries):
        try:
            return dialect.connect(*cargs, **cparams)
        except Exception as e:
            error_str = str(e)
            # Check for Azure SQL "not currently available" error (code 40613)
            if "40613" in error_str or "not currently available" in error_str.lower():
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Database is waking up from pause (attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {retry_delay} seconds..."
                    )
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 1.5, 15)  # Exponential backoff, max 15s
                    continue
            raise


# Register the retry handler for new connections
@event.listens_for(engine, "do_connect")
def receive_do_connect(dialect, conn_rec, cargs, cparams):
    return _connect_with_retry(dialect, conn_rec, cargs, cparams)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
