from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base
from sqlalchemy import ForeignKey

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    customer_contact = Column(String, nullable=False)
    item_description = Column(String, nullable=False)
    amount = Column(Float, nullable=False)

    # Stage tracking -- this is the core "scrutinizing" logic
    payment_status = Column(String, default="pending")     # pending -> confirmed
    delivery_status = Column(String, default="not_shipped") # not_shipped -> shipped -> delivered
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    overall_status = Column(String, default="open")         # open -> closed -> disputed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class TransactionEvent(Base):
    __tablename__ = "transaction_events"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    event_type = Column(String, nullable=False)  # e.g. "created", "payment_confirmed", "shipped", "delivered"
    note = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
