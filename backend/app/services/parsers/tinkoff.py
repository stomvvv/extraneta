"""
Тинькофф Путешествия parser — STUB

⚠️  THIS PARSER IS BASED ON ASSUMPTIONS.
    No real Tinkoff Travel export file was available.
    Verify against an actual export before production use.
    Update COLUMN_MAP below and remove this warning.
"""

import io
from datetime import date, datetime
from decimal import Decimal
import chardet
import pandas as pd

from app.models.booking import OTASource, PaymentStatus, BookingStatus
from app.services.parsers.base import BaseParser, ParseResult, ParsedBooking

COLUMN_MAP = {
    "booking_id": ["Номер заказа", "ID заказа", "booking_id", "Order ID"],
    "guest_name": ["Гость", "Имя", "ФИО гостя", "guest_name"],
    "check_in":   ["Дата заезда", "Заезд", "check_in", "Check-in"],
    "check_out":  ["Дата выезда", "Выезд", "check_out", "Check-out"],
    "room_type":  ["Тип номера", "Категория номера", "room_type"],
    "gross":      ["Стоимость", "Сумма заказа", "Оплачено", "Amount"],
    "net":        ["Выплата отелю", "К перечислению", "net_amount"],
    "commission": ["Комиссия", "Комиссия Тинькофф", "fee"],
    "rate":       ["Ставка комиссии", "% комиссии", "commission_rate"],
    "status":     ["Статус", "Статус заказа", "status"],
}

STATUS_MAP = {
    "подтверждён": BookingStatus.confirmed,
    "confirmed": BookingStatus.confirmed,
    "отменён": BookingStatus.cancelled,
    "cancelled": BookingStatus.cancelled,
}


def _find_col(df, candidates):
    for c in candidates:
        for col in df.columns:
            if col.strip().lower() == c.lower():
                return col
    return None


class TinkoffParser(BaseParser):
    OTA_SOURCE = OTASource.tinkoff

    def parse(self, file_bytes: bytes, filename: str) -> ParseResult:
        result = ParseResult()
        result.warnings.append(
            "⚠️ Тинькофф Путешествия parser is a stub — verify column names against a real export."
        )
        try:
            encoding = chardet.detect(file_bytes)["encoding"] or "utf-8"
            df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding, dtype=str, sep=None, engine="python") \
                if filename.lower().endswith(".csv") \
                else pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        except Exception as e:
            result.errors.append(str(e))
            return result

        cols = {k: _find_col(df, v) for k, v in COLUMN_MAP.items()}
        missing = [k for k in ("booking_id", "guest_name", "check_in", "check_out", "gross") if not cols[k]]
        if missing:
            result.errors.append(f"Тинькофф: missing columns {missing}. Found: {list(df.columns)}")
            return result

        for idx, row in df.iterrows():
            bid = str(row.get(cols["booking_id"], "")).strip()
            if not bid or bid in ("nan", ""):
                result.skipped += 1
                continue
            try:
                ci = self._pd(row.get(cols["check_in"]))
                co = self._pd(row.get(cols["check_out"]))
                if not ci or not co:
                    result.skipped += 1
                    continue
                nights = max((co - ci).days, 1)
                gross = self._parse_decimal(row.get(cols["gross"]))
                net = self._parse_decimal(row.get(cols["net"])) if cols["net"] else Decimal(0)
                comm = self._parse_decimal(row.get(cols["commission"])) if cols["commission"] else gross - net
                rate = self._parse_commission_rate(row.get(cols["rate"])) if cols["rate"] else (comm / gross * 100 if gross else Decimal(0))
                s_raw = str(row.get(cols["status"], "")).strip().lower() if cols["status"] else ""
                bs = STATUS_MAP.get(s_raw, BookingStatus.confirmed)
                ps = PaymentStatus.cancelled if bs == BookingStatus.cancelled else PaymentStatus.paid
                result.bookings.append(ParsedBooking(
                    source_ota=OTASource.tinkoff, booking_id_ota=bid,
                    guest_name=str(row.get(cols["guest_name"], "")).strip(),
                    check_in=ci, check_out=co, nights=nights,
                    gross_amount=gross, ota_commission_rate=rate,
                    ota_commission_amount=comm, net_amount=net or gross - comm,
                    payment_status=ps, booking_status=bs,
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
