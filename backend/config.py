import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATABASE_DIR = os.path.join(BASE_DIR, 'database')
os.makedirs(DATABASE_DIR, exist_ok=True)
DEFAULT_DB_PATH = os.path.join(DATABASE_DIR, 'traffic_dispatcher.db')

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'traffic-dispatcher-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DEFAULT_DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Exactly Five Fault Categories
    FAULT_CATEGORIES = [
        "Signal Light Failure",
        "Signal Timing Failure",
        "Controller / Electrical Failure",
        "Sensor / Detection Failure",
        "Communication / Network Failure"
    ]
    
    # Priority Levels & Deterministic Queue Ranks (Lower number = Higher precedence)
    PRIORITIES = {
        "EMERGENCY": 1,
        "CRITICAL": 2,
        "HIGH": 3,
        "MEDIUM": 4,
        "LOW": 5
    }
    
    # Report Statuses
    STATUSES = [
        "SUBMITTED",
        "VALIDATING",
        "PENDING",
        "ASSIGNED",
        "IN_PROGRESS",
        "ESCALATED",
        "RESOLVED",
        "REJECTED"
    ]
    
    # DFA & Regex Definitions for Report ID
    REPORT_ID_REGEX = r'^TSF-[0-9]{4}-[0-9]{5}$'
    REPORT_ID_PREFIX = 'TSF'
    
    # Fallback Central Queue Code
    CENTRAL_FALLBACK_QUEUE = 'CENTRAL_FALLBACK_QUEUE'

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
