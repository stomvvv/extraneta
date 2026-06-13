from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    ota = Column(String, nullable=False)
    status = Column(String, default="processing")  # processing | done | error
    records_total = Column(Integer, default=0)
    records_added = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    error_message = Column(String, default="")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
