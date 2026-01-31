from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base



class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True, index=True)   # auto-generated ID
    name = Column(String)
    phone = Column(String, unique=True)
    email = Column(String, unique=True)
    points = Column(Integer, default=0)

    purchases = relationship("Purchase", back_populates="customer")


class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))  # STRING
    amount = Column(Float)
    points_earned = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


    customer = relationship("Customer", back_populates="purchases")
