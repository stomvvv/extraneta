import io
import re
import chardet
from decimal import Decimal
import pandas as pd
from parsers.base import BaseParser, ParsedBooking


class AutoParser(BaseParser):
    """Universal fallback parser — tries to detect columns by keywords."""
    ota_key = "auto"

    CHECKIN_RE = re.compile(r"check.?in|заезд|arrival|from", re.I)
    CHECKOUT_RE = re.compile(r"check.?out|выезд|departure|to", re.I)
    AMOUNT_RE = re.compile(r"amount|сумма|стоимость|price|total", re.I)
    COMMISSION_RE = re.compile(r"commission|комиссия|вознаграждение|fee", re.I)
    GUEST_RE = re.compile(r"guest|гость|клиент|фио|name", re.I)
    ID_RE = re.compile(r"\bid\b|номер|booking.*id|reservation", re.I)

    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedBooking]:
        ext = filename.lower().rsplit(".", 1)[-1]
        if ext in ("xlsx", "xls"):
            df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        else:
            enc = chardet.detect(file_bytes)["encoding"] or "utf-8"
            for sep in (";", ",", "\t"):
                try:
                    df = pd.read_csv(io.BytesIO(file_bytes), sep=sep, encoding=enc, dtype=str)
                    if len(df.columns) > 2:
                        break
                except Exception:
                    continue
            else:
                raise ValueError("Не удалось распознать формат файла")

        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all")

        col_map = {}
        for col in df.columns:
            if self.ID_RE.search(col) and "id" not in col_map:
                col_map["id"] = col
            if self.GUEST_RE.search(col) and "guest" not in col_map:
                col_map["guest"] = col
            if self.CHECKIN_RE.search(col) and "check_in" not in col_map:
                col_map["check_in"] = col
            if self.CHECKOUT_RE.search(col) and "check_out" not in col_map:
                col_map["check_out"] = col
            if self.AMOUNT_RE.search(col) and "amount" not in col_map:
                col_map["amount"] = col
            if self.COMMISSION_RE.search(col) and "commission" not in col_map:
                col_map["commission"] = col

        if "check_in" not in col_map or "check_out" not in col_map:
            raise ValueError(
                "Не найдены колонки с датами заезда/выезда. "
                "Ожидаются колонки: check-in/check-out или заезд/выезд"
            )

        results = []
        for i, (_, row) in enumerate(df.iterrows()):
            row = row.fillna("")
            booking_id = str(row.get(col_map.get("id", ""), i + 1)).strip() or str(i + 1)
            guest = str(row.get(col_map.get("guest", ""), "")).strip()
            check_in = self.parse_date(row.get(col_map["check_in"], ""))
            check_out = self.parse_date(row.get(col_map["check_out"], ""))
            if not check_in or not check_out:
                continue
            gross = self.clean_amount(row.get(col_map.get("amount", ""), 0))
            comm_raw = self.clean_amount(row.get(col_map.get("commission", ""), 0))
            # Heuristic: if comm looks like a rate (< 100), treat it as %
            if comm_raw < Decimal("100") and gross:
                comm_rate = comm_raw
                comm_amt = (gross * comm_rate / Decimal("100")).quantize(Decimal("0.01"))
            else:
                comm_amt = comm_raw
                comm_rate = (comm_amt / gross * Decimal("100")).quantize(Decimal("0.01")) if gross else Decimal("0")
            net = gross - comm_amt
            results.append(ParsedBooking(
                booking_id_ota=booking_id,
                guest_name=guest,
                check_in=check_in,
                check_out=check_out,
                gross_amount=gross,
                ota_commission_rate=comm_rate,
                ota_commission_amount=comm_amt,
                net_amount=net,
                raw_row={str(k): str(v) for k, v in row.to_dict().items()},
            ))
        return results
