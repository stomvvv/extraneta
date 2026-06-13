from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from database import Base


class CommissionSetting(Base):
    __tablename__ = "commission_settings"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    ota = Column(String, nullable=False)
    expected_rate = Column(Numeric(5, 2), default=15.0)
