"""
Yandex Travel (Яндекс Путешествия) parser.

File format (confirmed from real Payment_Details_XXXXXXXXXX.xlsx files):
  Row 0  : Payment batch ID (sheet name = same ID)
  Row 1  : Empty
  Row 2  : Column headers
  Row 3+ : Data rows (until empty rows)
  Last   : Legal disclaimer text

Columns (0-indexed):
  0  Объект размещения        → hotel_name_from_file
  1  № Яндекс                 → booking_id_ota  (YA-XXXX-XXXX-XXXX)
  2  Имя гостя                → guest_name
  3  Дата брони               → booking_date    (YYYY-MM-DD)
  4  Заезд                    → check_in        (YYYY-MM-DD)
  5  Выезд                    → check_out       (YYYY-MM-DD)
  6  Тип перечисления         → payment_status  (Оплата=paid, Возврат=refunded)
  7  Оплатил гость, ₽         → gross_amount
  8  Перечислено отелю, ₽     → net_amount
  9  Вознаграждение Яндекса…  → ota_commission_amount
  10 Ставка вознаграждения    → ota_commission_rate  ("15.00%")

Notes:
  - No room_type in this export
  - Negative amounts represent refunds (Возврат)
  - Dates are already ISO format (YYYY-MM-DD) — no conversion needed
  - Multi-property: single file may contain rows for multiple hotel names
"""

import io
from datetime import date, datetime
from decimal import Decimal

import pandas as pd

from app.models.booking import OTASource, PaymentStatus, BookingStatus
from app.services.parsers.base import BaseParser, ParseResult, ParsedBooking

HEADER_ROW = 2  # 0-indexed

COL_HOTEL_NAME = "Объект размещения"
COL_BOOKING_ID = "№ Яндекс"
COL_GUEST_NAME = "Имя гостя"
COL_BOOKING_DATE = "Дата брони"
COL_CHECK_IN = "Заезд"
COL_CHECK_OUT = "Выезд"
COL_TRANSFER_TYPE = "Тип перечисления"
COL_GROSS = "Оплатил гость, ₽"
COL_NET = "Перечислено отелю, ₽"
COL_COMMISSION = "Вознаграждение Яндекса с учетом скидки по совместной акции"
COL_COMMISSION_RATE = "Ставка вознаграждения"

# Fallback partial matches for column name variants
COMMISSION_PARTIAL = "Вознаграждение Яндекса"


class YandexParser(BaseParser):
    OTA_SOURCE = OTASource.yandex

    def parse(self, file_bytes: bytes, filename: str) -> ParseResult:
        result = ParseResult()
        try:
            df = pd.read_excel(
                io.BytesIO(file_bytes),
                header=HEADER_ROW,
                dtype=str,
            )
        except Exception as e:
            result.errors.append(f"Failed to read Excel file: {e}")
            return result

        # Resolve commission column (name is very long and may vary slightly)
        commission_col = None
        for col in df.columns:
            if COMMISSION_PARTIAL in str(col):
                commission_col = col
                break
        if commission_col is None:
            result.errors.append(
                f"Cannot find commission column (expected to contain '{COMMISSION_PARTIAL}'). "
                f"Available columns: {list(df.columns)}"
            )
            return result

        required = [COL_BOOKING_ID, COL_GUEST_NAME, COL_CHECK_IN, COL_CHECK_OUT,
                    COL_GROSS, COL_NET, COL_COMMISSION_RATE]
        missing = [c for c in required if c not in df.columns]
        if missing:
            result.errors.append(f"Missing required columns: {missing}. Found: {list(df.columns)}")
            return result

        for idx, row in df.iterrows():
            booking_id = str(row.get(COL_BOOKING_ID, "")).strip()
            # Skip empty rows and disclaimer row
            if not booking_id or booking_id in ("nan", "None", "") or not booking_id.startswith("YA-"):
                result.skipped += 1
                continue

            try:
                check_in = self._parse_date(row.get(COL_CHECK_IN))
                check_out = self._parse_date(row.get(COL_CHECK_OUT))
                booking_date = self._parse_date(row.get(COL_BOOKING_DATE))

                if check_in is None or check_out is None:
                    result.warnings.append(f"Row {idx}: missing check_in/check_out for {booking_id}, skipped")
                    result.skipped += 1
                    continue

                nights = max((check_out - check_in).days, 1)

                gross = self._parse_decimal(row.get(COL_GROSS))
                net = self._parse_decimal(row.get(COL_NET))
                commission_amount = self._parse_decimal(row.get(commission_col))
                commission_rate = self._parse_commission_rate(row.get(COL_COMMISSION_RATE))

                transfer_type = str(row.get(COL_TRANSFER_TYPE, "")).strip()
                if transfer_type == "Возврат":
                    payment_status = PaymentStatus.refunded
                    booking_status = BookingStatus.cancelled
                    # Ensure amounts are negative for refunds
                    gross = -abs(gross)
                    net = -abs(net)
                    commission_amount = -abs(commission_amount)
                else:
                    payment_status = PaymentStatus.paid
                    booking_status = BookingStatus.confirmed

                hotel_name = str(row.get(COL_HOTEL_NAME, "")).strip()
                if hotel_name in ("nan", "None"):
                    hotel_name = None

                booking = ParsedBooking(
                    source_ota=OTASource.yandex,
                    booking_id_ota=booking_id,
                    guest_name=str(row.get(COL_GUEST_NAME, "")).strip(),
                    booking_date=booking_date,
                    check_in=check_in,
                    check_out=check_out,
                    nights=nights,
                    gross_amount=gross,
                    ota_commission_rate=commission_rate,
                    ota_commission_amount=commission_amount,
                    net_amount=net,
                    currency="RUB",
                    payment_status=payment_status,
                    booking_status=booking_status,
                    hotel_name_from_file=hotel_name,
                )
                result.bookings.append(booking)
            except Exception as e:
                result.warnings.append(f"Row {idx}: parse error for {booking_id}: {e}")
                result.skipped += 1

        return result

    def _parse_date(self, value) -> date | None:
        if value is None or str(value).strip() in ("nan", "None", ""):
            return None
        s = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s.split(" ")[0] if " " in s else s, fmt).date()
            except ValueError:
                continue
        # Try pandas timestamp
        try:
            return pd.to_datetime(s).date()
        except Exception:
            return None
