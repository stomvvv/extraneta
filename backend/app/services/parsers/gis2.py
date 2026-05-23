"""
2ГИС parser — STUB

⚠️  THIS PARSER IS BASED ON ASSUMPTIONS.
    No real 2ГИС export file was available. Verify and update COLUMN_MAP before production use.
"""

import io
from datetime import date, datetime
from decimal import Decimal
import chardet
import pandas as pd

from app.models.booking import OTASource, PaymentStatus, BookingStatus
from app.services.parsers.base import BaseParser, ParseResult, ParsedBooking

COLUMN_MAP = {
    "booking_id": ["ID брони", "Номер брони", "booking_id"],
    "guest_name": ["Гость", "ФИО", "Имя гостя"],
    "check_in":   ["Дата заезда", "Заезд"],
    "check_out":  ["Дата выезда", "Выезд"],
    "room_type":  ["Тип номера"],
    "gross":      ["Стоимость", "Сумма"],
    "net":        ["К выплате", "Выплата"],
    "commission": ["Комиссия 2ГИС", "Комиссия"],
    "rate":       ["% комиссии", "Ставка"],
    "status":     ["Статус"],
}


def _find_col(df, cands):
    for c in cands:
        for col in df.columns:
            if col.strip().lower() == c.lower():
                return col
    return None


class Gis2Parser(BaseParser):
    OTA_SOURCE = OTASource.gis2

    def parse(self, file_bytes: bytes, filename: str) -> ParseResult:
        result = ParseResult()
        result.warnings.append("⚠️ 2ГИС parser is a stub — verify column names against a real export.")
        try:
            enc = chardet.detect(file_bytes)["encoding"] or "utf-8"
            df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc, dtype=str, sep=None, engine="python") \
                if filename.lower().endswith(".csv") \
                else pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        except Exception as e:
            result.errors.append(str(e))
            return result

        cols = {k: _find_col(df, v) for k, v in COLUMN_MAP.items()}
        missing = [k for k in ("booking_id", "guest_name", "check_in", "check_out", "gross") if not cols[k]]
        if missing:
            result.errors.append(f"2ГИС: missing {missing}. Found: {list(df.columns)}")
            return result

        for idx, row in df.iterrows():
            bid = str(row.get(cols["booking_id"], "")).strip()
            if not bid or bid in ("nan", ""):
                result.skipped += 1
                continue
            try:
                ci, co = self._pd(row.get(cols["check_in"])), self._pd(row.get(cols["check_out"]))
                if not ci or not co:
                    result.skipped += 1
                    continue
                nights = max((co - ci).days, 1)
                gross = self._parse_decimal(row.get(cols["gross"]))
                net = self._parse_decimal(row.get(cols["net"])) if cols["net"] else Decimal(0)
                comm = self._parse_decimal(row.get(cols["commission"])) if cols["commission"] else gross - net
                rate = self._parse_commission_rate(row.get(cols["rate"])) if cols["rate"] else (comm / gross * 100 if gross else Decimal(0))
                result.bookings.append(ParsedBooking(
                    source_ota=OTASource.gis2, booking_id_ota=bid,
                    guest_name=str(row.get(cols["guest_name"], "")).strip(),
                    check_in=ci, check_out=co, nights=nights,
                    gross_amount=gross, ota_commission_rate=rate,
                    ota_commission_amount=comm, net_amount=net or gross - comm,
                    payment_status=PaymentStatus.paid, booking_status=BookingStatus.confirmed,
                    room_type=str(row.get(cols["room_type"], "")).strip() if cols["room_type"] else None,
                ))
            except Exception as e:
                result.warnings.append(f"Row {idx}: {e}")
                result.skipped += 1
        return result

    def _pd(self, v) -> date | None:
        if not v or str(v).strip() in ("nan", "None", ""):
            return None
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(str(v).strip(), fmt).date()
            except ValueError:
                pass
        try:
            return pd.to_datetime(str(v)).date()
        except Exception:
            return None
