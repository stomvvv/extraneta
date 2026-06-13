from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
