from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional
from app.models.booking import OTASource, PaymentStatus, BookingStatus


@dataclass
class ParsedBooking:
    booking_id_ota: str
    guest_name: str
    check_in: date
    check_out: date
    nights: int
    gross_amount: Decimal
    ota_commission_rate: Decimal
    ota_commission_amount: Decimal
    net_amount: Decimal
    payment_status: PaymentStatus
    booking_status: BookingStatus
    source_ota: OTASource
    room_type: Optional[str] = None
    booking_date: Optional[date] = None
    currency: str = "RUB"
    has_vat: bool = False
    hotel_name_from_file: Optional[str] = None


@dataclass
class ParseResult:
    bookings: list[ParsedBooking] = field(default_factory=list)
    skipped: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class BaseParser(ABC):
    """
    Each OTA parser receives raw file bytes and returns a ParseResult.
    All parsers must normalize data into the common ParsedBooking structure.
    """

    OTA_SOURCE: OTASource

    @abstractmethod
    def parse(self, file_bytes: bytes, filename: str) -> ParseResult:
        ...

    def _parse_decimal(self, value) -> Decimal:
        if value is None:
            return Decimal("0")
        s = str(value).strip().replace(" ", "").replace(",", ".").replace("₽", "").replace("%", "")
        try:
            return Decimal(s)
        except Exception:
            return Decimal("0")

    def _parse_commission_rate(self, value) -> Decimal:
        """Parse '15.00%' or '0.15' or '15.0' → Decimal('15.0')"""
        s = str(value).strip().replace("%", "").replace(",", ".")
        try:
            d = Decimal(s)
            # If given as fraction (0.15), convert to percent
            if d <= 1:
                d = d * 100
            return d
        except Exception:
            return Decimal("0")
