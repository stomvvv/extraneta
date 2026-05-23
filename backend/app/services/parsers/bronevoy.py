"""
Броневик (Bronevoy) parser — STUB

⚠️  THIS PARSER IS BASED ON ASSUMPTIONS.
    No real Броневик export file was available during initial development.
    Verify column names against an actual Броневик report before using in production.

Assumed format: XLSX report from bronevoy.ru extranet
To update: adjust COLUMN_MAP below and remove this warning.
"""

import io
import chardet
from datetime import date, datetime
from decimal import Decimal

import pandas as pd

from app.models.booking import OTASource, PaymentStatus, BookingStatus
from app.services.parsers.base import BaseParser, ParseResult, ParsedBooking

# ── ADJUST THESE when real file is available ──────────────────────────────────
COLUMN_MAP = {
    "booking_id": ["Номер брони", "ID брони", "booking_id", "Бронь №"],
    "guest_name": ["Гость", "Имя гостя", "ФИО", "guest_name"],
    "check_in":   ["Дата заезда", "Заезд", "check_in", "Дата въезда"],
    "check_out":  ["Дата выезда", "Выезд", "check_out", "Дата выезда"],
    "room_type":  ["Тип номера", "Категория", "room_type"],
    "gross":      ["Стоимость брони", "Сумма брони", "Оплачено", "Стоимость"],
    "net":        ["К выплате", "Выплата", "Чистая сумма", "net_amount"],
    "commission": ["Комиссия", "Комиссия Броневик", "Сумма комиссии"],
    "rate":       ["% Комиссии", "Ставка", "Комиссия %", "commission_rate"],
    "status":     ["Статус", "Статус брони", "status"],
}

STATUS_MAP = {
    "подтверждена": BookingStatus.confirmed,
    "отменена": BookingStatus.cancelled,
    "выполнена": BookingStatus.confirmed,
    "no_show": BookingStatus.no_show,
}
# ─────────────────────────────────────────────────────────────────────────────


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        for col in df.columns:
            if col.strip().lower() == c.lower():
                return col
    return None


class BronevoyParser(BaseParser):
    OTA_SOURCE = OTASource.bronevoy

    def parse(self, file_bytes: bytes, filename: str) -> ParseResult:
        result = ParseResult()
        result.warnings.append(
            "⚠️ Броневик parser is a stub — column names are assumed. "
            "Verify against a real Броневик export file."
        )

        try:
            encoding = chardet.detect(file_bytes)["encoding"] or "utf-8"
            if filename.lower().endswith(".csv"):
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=encoding, dtype=str, sep=None, engine="python")
            else:
                df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        except Exception as e:
            result.errors.append(f"Failed to read file: {e}")
            return result

        cols = {key: _find_column(df, candidates) for key, candidates in COLUMN_MAP.items()}
        missing = [k for k, v in cols.items() if v is None and k in ("booking_id", "guest_name", "check_in", "check_out", "gross")]
        if missing:
            result.errors.append(
                f"Броневик: cannot find required columns {missing}. "
                f"Found: {list(df.columns)}. Update COLUMN_MAP in bronevoy.py."
            )
            return result

        for idx, row in df.iterrows():
            booking_id = str(row.get(cols["booking_id"], "")).strip()
            if not booking_id or booking_id in ("nan", "None", ""):
                result.skipped += 1
                continue
            try:
                check_in = self._parse_date(row.get(cols["check_in"]))
                check_out = self._parse_date(row.get(cols["check_out"]))
                if not check_in or not check_out:
                    result.skipped += 1
                    continue
                nights = max((check_out - check_in).days, 1)
                gross = self._parse_decimal(row.get(cols["gross"]))
                net = self._parse_decimal(row.get(cols["net"])) if cols["net"] else Decimal("0")
                commission = self._parse_decimal(row.get(cols["commission"])) if cols["commission"] else gross - net
                rate = self._parse_commission_rate(row.get(cols["rate"])) if cols["rate"] else (
                    commission / gross * 100 if gross else Decimal("0")
                )
                status_raw = str(row.get(cols["status"], "")).strip().lower() if cols["status"] else ""
                booking_status = STATUS_MAP.get(status_raw, BookingStatus.confirmed)
                payment_status = PaymentStatus.cancelled if booking_status == BookingStatus.cancelled else PaymentStatus.paid

                result.bookings.append(ParsedBooking(
                    source_ota=OTASource.bronevoy,
                    booking_id_ota=booking_id,
                    guest_name=str(row.get(cols["guest_name"], "")).strip(),
                    check_in=check_in,
                    check_out=check_out,
                    nights=nights,
                    gross_amount=gross,
                    ota_commission_rate=rate,
                    ota_commission_amount=commission,
                    net_amount=net if net else gross - commission,
                    payment_status=payment_status,
                    booking_status=booking_status,
                    room_type=str(row.get(cols["room_type"], "")).strip() if cols["room_type"] else None,
                ))
            except Exception as e:
                result.warnings.append(f"Row {idx}: {e}")
                result.skipped += 1
        return result

    def _parse_date(self, value) -> date | None:
        if not value or str(value).strip() in ("nan", "None", ""):
            return None
        s = str(value).strip()
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
        try:
            return pd.to_datetime(s).date()
        except Exception:
            return None
