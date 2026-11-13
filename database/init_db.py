import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from config import Config, DEFAULT_DB_PATH
from app.models.schema import Base

def init_database(db_path=DEFAULT_DB_PATH):
    print(f"[*] Initializing database at: {db_path}")
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    print("[+] All database tables created successfully.")
    return engine

if __name__ == "__main__":
    init_database()
