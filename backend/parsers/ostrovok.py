import io
from decimal import Decimal
import pandas as pd
from parsers.base import BaseParser, ParsedBooking


class OstrovokParser(BaseParser):
    ota_key = "ostrovok"

    def parse(self, file_bytes: bytes, filename: str) -> list[ParsedBooking]:
        df = pd.read_excel(io.BytesIO(file_bytes), dtype=str)
        df.columns = [str(c).strip().lower() for c in df.columns]
        df = df.dropna(how="all")

        results = []
        for _, row in df.iterrows():
            row = row.fillna("")
            booking_id = self._find(row, ["reservation id", "booking id", "id", "номер"])
            if not booking_id:
                continue
            guest = self._find(row, ["guest name", "name", "гость", "клиент"])
            check_in = self.parse_date(self._find(row, ["check-in", "check in", "checkin", "заезд"]))
            check_out = self.parse_date(self._find(row, ["check-out", "check out", "checkout", "выезд"]))
            if not check_in or not check_out:
                continue
            gross = self.clean_amount(self._find(row, ["price", "amount", "total", "сумма", "стоимость"]))
            comm_rate = self.clean_amount(self._find(row, ["commission %", "commission rate", "комиссия %"]))
            comm_amt = self.clean_amount(self._find(row, ["commission", "комиссия"]))
            if comm_rate and not comm_amt and gross:
                comm_amt = (gross * comm_rate / Decimal("100")).quantize(Decimal("0.01"))
            elif comm_amt and not comm_rate and gross:
                comm_rate = (comm_amt / gross * Decimal("100")).quantize(Decimal("0.01")) if gross else Decimal("0")
            net = gross - comm_amt
            status_raw = self._find(row, ["status", "статус"])
            results.append(ParsedBooking(
                booking_id_ota=str(booking_id).strip(),
                guest_name=str(guest).strip(),
                check_in=check_in,
                check_out=check_out,
                gross_amount=gross,
                ota_commission_rate=comm_rate,
                ota_commission_amount=comm_amt,
                net_amount=net,
                booking_status=self.detect_status(status_raw),
                raw_row=row.to_dict(),
            ))
        return results

    @staticmethod
    def _find(row, keys):
        for k in keys:
            for col in row.index:
                if k in str(col).lower():
                    v = row[col]
                    if v and str(v).strip():
                        return v
        return ""
