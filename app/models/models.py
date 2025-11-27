from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Operator(Base):
    __tablename__ = "operators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    max_load = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    requests = relationship("Request", back_populates="operator")
    source_weights = relationship("OperatorSourceWeight", back_populates="operator")

    def get_current_load(self, db):
        """Calculate current load based on active requests"""
        from sqlalchemy import func
        return db.query(func.count(Request.id)).filter(
            Request.operator_id == self.id,
            Request.status == "active"
        ).scalar() or 0


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    requests = relationship("Request", back_populates="lead")


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    requests = relationship("Request", back_populates="source")
    operator_weights = relationship("OperatorSourceWeight", back_populates="source")


class OperatorSourceWeight(Base):
    __tablename__ = "operator_source_weights"

    id = Column(Integer, primary_key=True, index=True)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    weight = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    operator = relationship("Operator", back_populates="source_weights")
    source = relationship("Source", back_populates="operator_weights")


class Request(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    operator_id = Column(Integer, ForeignKey("operators.id"), nullable=True)
    status = Column(String, default="active")
    message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="requests")
    source = relationship("Source", back_populates="requests")
    operator = relationship("Operator", back_populates="requests")
