from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional
import re
from dateutil import parser as dateutil_parser


@dataclass
class ParsedBooking:
    booking_id_ota: str
    guest_name: str
    check_in: date
    check_out: date
    gross_amount: Decimal
    ota_commission_rate: Decimal
    ota_commission_amount: Decimal
    net_amount: Decimal
    booking_status: str = "confirmed"
    room_type: str = ""
    payment_status: str = "paid"
    raw_row: dict = field(default_factory=dict)


class BaseParser:
    ota_key: str = ""

    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedBooking]:
        raise NotImplementedError

    @staticmethod
    def clean_amount(value) -> Decimal:
        if value is None:
            return Decimal("0")
        s = str(value).strip()
        s = re.sub(r"[^\d,.\-]", "", s)
        s = s.replace(",", ".")
        if not s or s == "-":
            return Decimal("0")
        try:
            return Decimal(s).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0")

    @staticmethod
    def parse_date(value) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, date):
            return value
        s = str(value).strip()
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                from datetime import datetime
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
        try:
            return dateutil_parser.parse(s, dayfirst=True).date()
        except Exception:
            return None

    @staticmethod
    def calc_nights(check_in: date, check_out: date) -> int:
        delta = (check_out - check_in).days
        return max(delta, 1)

    @staticmethod
    def detect_status(value: str) -> str:
        if not value:
            return "confirmed"
        v = str(value).lower()
        if any(w in v for w in ["отмен", "cancel", "аннул"]):
            return "cancelled"
        if any(w in v for w in ["no_show", "no show", "неявк"]):
            return "no_show"
        return "confirmed"
