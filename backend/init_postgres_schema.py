"""
Initialize PostgreSQL schema for production RAG system
"""
from database.postgres_vector_db import PostgresVectorDB
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Initialize database schema"""
    try:
        # Connection string for local PostgreSQL
        conn_str = "postgresql://qsp_user:qsp_secure_pass@localhost:5432/qsp_compliance"
        
        logger.info("Connecting to PostgreSQL...")
        db = PostgresVectorDB(connection_string=conn_str)
        
        logger.info("Initializing schema...")
        db.initialize_schema()
        
        logger.info("✅ Schema initialized successfully!")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize schema: {e}")
        raise

if __name__ == "__main__":
    main()
