from datetime import datetime
import json
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    role = Column(String(32), nullable=False, default='reporter')  # admin, handler, reporter
    full_name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Zone(Base):
    __tablename__ = 'zones'
    
    id = Column(Integer, primary_key=True)
    zone_code = Column(String(32), unique=True, nullable=False, index=True) # ZONE-A .. ZONE-E
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    
    handlers = relationship("Handler", back_populates="zone")
    reports = relationship("Report", back_populates="zone")
    routing_rules = relationship("RoutingRule", back_populates="zone")

    def to_dict(self):
        return {
            "id": self.id,
            "zone_code": self.zone_code,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active
        }

class Handler(Base):
    __tablename__ = 'handlers'
    
    id = Column(Integer, primary_key=True)
    handler_code = Column(String(32), unique=True, nullable=False, index=True) # HND-001
    name = Column(String(128), nullable=False)
    email = Column(String(128), nullable=True)
    phone = Column(String(32), nullable=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=True)
    supported_categories = Column(Text, nullable=False, default="[]") # JSON list of strings
    is_available = Column(Boolean, default=True)
    max_capacity = Column(Integer, default=5)
    current_workload = Column(Integer, default=0)
    is_backup_eligible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    zone = relationship("Zone", back_populates="handlers")
    assignments = relationship("Assignment", back_populates="handler")

    def get_supported_categories(self):
        try:
            return json.loads(self.supported_categories) if self.supported_categories else []
        except Exception:
            return []

    def set_supported_categories(self, cats):
        self.supported_categories = json.dumps(cats)

    def to_dict(self):
        return {
            "id": self.id,
            "handler_code": self.handler_code,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "zone_id": self.zone_id,
            "zone_code": self.zone.zone_code if self.zone else None,
            "zone_name": self.zone.name if self.zone else "Unassigned",
            "supported_categories": self.get_supported_categories(),
            "is_available": self.is_available,
            "max_capacity": self.max_capacity,
            "current_workload": self.current_workload,
            "remaining_capacity": max(0, self.max_capacity - self.current_workload),
            "is_backup_eligible": self.is_backup_eligible,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Report(Base):
    __tablename__ = 'reports'
    
    id = Column(Integer, primary_key=True)
    report_code = Column(String(32), unique=True, nullable=False, index=True) # e.g. TSF-2026-00001
    reporter_name = Column(String(128), nullable=False)
    reporter_contact = Column(String(64), nullable=False)
    signal_id = Column(String(64), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=True)
    zone_raw = Column(String(64), nullable=True)
    location = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(128), nullable=False)
    priority = Column(String(32), nullable=False, default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL, EMERGENCY
    status = Column(String(32), nullable=False, default="SUBMITTED")
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    zone = relationship("Zone", back_populates="reports")
    assignments = relationship("Assignment", back_populates="report", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="report", cascade="all, delete-orphan")
    dispatch_logs = relationship("DispatchLog", back_populates="report", cascade="all, delete-orphan")
    classification_logs = relationship("ClassificationLog", back_populates="report", cascade="all, delete-orphan")

    def to_dict(self):
        active_assignment = None
        for a in self.assignments:
            if a.status == 'ACTIVE':
                active_assignment = a.to_dict()
                break

        return {
            "id": self.id,
            "report_code": self.report_code,
            "reporter_name": self.reporter_name,
            "reporter_contact": self.reporter_contact,
            "signal_id": self.signal_id,
            "zone_id": self.zone_id,
            "zone_code": self.zone.zone_code if self.zone else self.zone_raw,
            "zone_name": self.zone.name if self.zone else "Unknown / Unresolved Zone",
            "zone_raw": self.zone_raw,
            "location": self.location,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "active_assignment": active_assignment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class RoutingRule(Base):
    __tablename__ = 'routing_rules'
    
    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey('zones.id'), nullable=False)
    category = Column(String(128), nullable=False)
    primary_handler_id = Column(Integer, ForeignKey('handlers.id'), nullable=False)
    backup_handler_id = Column(Integer, ForeignKey('handlers.id'), nullable=True)
    escalation_path = Column(String(128), default="SUPERVISOR_ESCALATION")
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        UniqueConstraint('zone_id', 'category', name='uix_zone_category'),
    )

    zone = relationship("Zone", back_populates="routing_rules")
    primary_handler = relationship("Handler", foreign_keys=[primary_handler_id])
    backup_handler = relationship("Handler", foreign_keys=[backup_handler_id])

    def to_dict(self):
        return {
            "id": self.id,
            "zone_id": self.zone_id,
            "zone_code": self.zone.zone_code if self.zone else None,
            "zone_name": self.zone.name if self.zone else None,
            "category": self.category,
            "primary_handler_id": self.primary_handler_id,
            "primary_handler_name": self.primary_handler.name if self.primary_handler else None,
            "backup_handler_id": self.backup_handler_id,
            "backup_handler_name": self.backup_handler.name if self.backup_handler else "None Configured",
            "escalation_path": self.escalation_path,
            "is_active": self.is_active
        }

class Assignment(Base):
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
    handler_id = Column(Integer, ForeignKey('handlers.id'), nullable=True, index=True) # Null if escalated/waiting queue
    assigned_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="ACTIVE") # ACTIVE, COMPLETED, REASSIGNED, CANCELLED
    reassigned_from_id = Column(Integer, ForeignKey('assignments.id'), nullable=True)
    assignment_type = Column(String(32), default="PRIMARY") # PRIMARY, BACKUP, ESCALATION, QUEUED, MANUAL
    completed_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    report = relationship("Report", back_populates="assignments")
    handler = relationship("Handler", back_populates="assignments")

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "report_code": self.report.report_code if self.report else None,
            "handler_id": self.handler_id,
            "handler_name": self.handler.name if self.handler else "None (Escalated/Queued)",
            "handler_code": self.handler.handler_code if self.handler else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "status": self.status,
            "assignment_type": self.assignment_type,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "resolution_notes": self.resolution_notes
        }

class StatusHistory(Base):
    __tablename__ = 'status_history'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
    previous_status = Column(String(32), nullable=True)
    new_status = Column(String(32), nullable=False)
    updated_by = Column(String(128), nullable=False)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    report = relationship("Report", back_populates="status_history")

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "previous_status": self.previous_status,
            "new_status": self.new_status,
            "updated_by": self.updated_by,
            "remarks": self.remarks,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class DispatchLog(Base):
    __tablename__ = 'dispatch_logs'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
    decision = Column(String(64), nullable=False) # ASSIGNED_PRIMARY, ASSIGNED_BACKUP, ESCALATED_EMERGENCY, QUEUED_CAPACITY, FALLBACK_UNKNOWN_ZONE, REJECTED
    reason = Column(Text, nullable=False)
    primary_handler_id = Column(Integer, ForeignKey('handlers.id'), nullable=True)
    assigned_handler_id = Column(Integer, ForeignKey('handlers.id'), nullable=True)
    is_backup = Column(Boolean, default=False)
    is_escalated = Column(Boolean, default=False)
    is_queued = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    report = relationship("Report", back_populates="dispatch_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "report_code": self.report.report_code if self.report else None,
            "decision": self.decision,
            "reason": self.reason,
            "primary_handler_id": self.primary_handler_id,
            "assigned_handler_id": self.assigned_handler_id,
            "is_backup": self.is_backup,
            "is_escalated": self.is_escalated,
            "is_queued": self.is_queued,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class ClassificationLog(Base):
    __tablename__ = 'classification_logs'
    
    id = Column(Integer, primary_key=True)
    report_id = Column(Integer, ForeignKey('reports.id'), nullable=False, index=True)
    detected_category = Column(String(128), nullable=False)
    matched_categories = Column(Text, nullable=False, default="[]") # JSON array of matched categories with details
    confidence_score = Column(Float, default=1.0)
    resolution_rule = Column(String(256), nullable=False)
    is_manual_override = Column(Boolean, default=False)
    overridden_by = Column(String(128), nullable=True)
    original_category = Column(String(128), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    report = relationship("Report", back_populates="classification_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "report_code": self.report.report_code if self.report else None,
            "detected_category": self.detected_category,
            "matched_categories": json.loads(self.matched_categories) if self.matched_categories else [],
            "confidence_score": self.confidence_score,
            "resolution_rule": self.resolution_rule,
            "is_manual_override": self.is_manual_override,
            "overridden_by": self.overridden_by,
            "original_category": self.original_category,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
