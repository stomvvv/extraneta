from decimal import Decimal
from app.models.booking import Booking, PaymentStatus, BookingStatus


class AnomalyDetector:
    """
    Checks a single booking against business rules and returns a list of reason strings.
    An empty list means no anomalies.
    """

    @staticmethod
    def check(booking: Booking, expected_rates: dict[str, float]) -> list[str]:
        reasons = []

        ota_key = booking.source_ota.value
        gross = booking.gross_amount
        commission = booking.ota_commission_amount
        rate = booking.ota_commission_rate

        # 1. Commission rate vs expected (tolerance: 1 percentage point)
        if ota_key in expected_rates:
            expected = Decimal(str(expected_rates[ota_key]))
            deviation = abs(rate - expected)
            if deviation > Decimal("1.0"):
                reasons.append(
                    f"Commission rate {rate}% deviates from expected {expected}% "
                    f"by {deviation:.2f}pp"
                )

        # 2. Invalid commission amounts
        if gross > 0:
            if commission < 0:
                reasons.append("Negative commission amount on non-refund booking")
            elif commission == 0 and rate > 0:
                reasons.append("Zero commission amount but rate is non-zero")

        # 3. Cancelled booking with unreturned commission
        if (
            booking.booking_status == BookingStatus.cancelled
            and booking.payment_status != PaymentStatus.refunded
            and commission > 0
        ):
            reasons.append("Booking cancelled but commission not refunded")

        # 4. Suspiciously high commission (> 40% seems wrong)
        if gross > 0 and commission > 0:
            actual_rate = (commission / gross) * 100
            if actual_rate > Decimal("40"):
                reasons.append(f"Unusually high commission rate: {actual_rate:.1f}%")

        # 5. Net + commission should equal gross (within 1 kopek tolerance)
        if gross > 0:
            calculated_net = gross - commission
            diff = abs(booking.net_amount - calculated_net)
            if diff > Decimal("0.10"):
                reasons.append(
                    f"Net amount mismatch: {booking.net_amount} ≠ gross({gross}) - commission({commission}) = {calculated_net}"
                )

        return reasons
