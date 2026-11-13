from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from config import Config

_engine = None
_session_factory = None

def get_engine(db_uri=None):
    global _engine
    if _engine is None or db_uri:
        uri = db_uri or Config.SQLALCHEMY_DATABASE_URI
        _engine = create_engine(uri, echo=False)
    return _engine

def get_session(db_uri=None):
    engine = get_engine(db_uri)
    factory = sessionmaker(bind=engine, autoflush=False)
    return factory()
