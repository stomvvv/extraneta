from decimal import Decimal
from parsers.base import ParsedBooking


def detect_anomalies(booking: ParsedBooking, expected_rate: float) -> tuple[bool, str]:
    reasons = []

    rate = float(booking.ota_commission_rate)
    if abs(rate - expected_rate) > 1.0:
        reasons.append(f"Комиссия {rate}% ≠ ожидаемой {expected_rate}%")

    if float(booking.gross_amount) <= 0:
        reasons.append("Нулевая или отрицательная сумма")

    if booking.booking_status == "cancelled" and float(booking.ota_commission_amount) > 0:
        reasons.append("Отменённая бронь, но комиссия не возвращена")

    return bool(reasons), "; ".join(reasons)
