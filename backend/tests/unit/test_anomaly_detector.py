import pytest
from decimal import Decimal
from unittest.mock import MagicMock
from app.services.anomaly import AnomalyDetector
from app.models.booking import Booking, BookingStatus, PaymentStatus, OTASource


def _booking(**kwargs):
    b = MagicMock(spec=Booking)
    b.source_ota = kwargs.get("source_ota", OTASource.yandex)
    b.gross_amount = Decimal(str(kwargs.get("gross", "10000")))
    b.ota_commission_amount = Decimal(str(kwargs.get("commission", "1500")))
    b.ota_commission_rate = Decimal(str(kwargs.get("rate", "15")))
    b.net_amount = Decimal(str(kwargs.get("net", "8500")))
    b.booking_status = kwargs.get("booking_status", BookingStatus.confirmed)
    b.payment_status = kwargs.get("payment_status", PaymentStatus.paid)
    return b


class TestAnomalyDetector:
    def test_no_anomaly_normal_booking(self):
        b = _booking(gross=10000, commission=1500, rate=15, net=8500)
        reasons = AnomalyDetector.check(b, {"yandex": 15.0})
        assert reasons == []

    def test_rate_deviation_triggers_anomaly(self):
        # Expected 15%, actual 20% → 5pp deviation > 1pp threshold
        b = _booking(gross=10000, commission=2000, rate=20, net=8000)
        reasons = AnomalyDetector.check(b, {"yandex": 15.0})
        assert any("deviates" in r for r in reasons)

    def test_rate_deviation_within_tolerance(self):
        # Expected 15%, actual 15.5% → 0.5pp < 1pp → no anomaly
        b = _booking(gross=10000, commission=1550, rate=15.5, net=8450)
        reasons = AnomalyDetector.check(b, {"yandex": 15.0})
        assert not any("deviates" in r for r in reasons)

    def test_cancelled_with_unreturned_commission(self):
        b = _booking(
            gross=10000, commission=1500, rate=15, net=8500,
            booking_status=BookingStatus.cancelled,
            payment_status=PaymentStatus.paid,
        )
        reasons = AnomalyDetector.check(b, {})
        assert any("commission not refunded" in r for r in reasons)

    def test_zero_commission_with_nonzero_rate(self):
        b = _booking(gross=10000, commission=0, rate=15, net=10000)
        reasons = AnomalyDetector.check(b, {})
        assert any("Zero commission" in r for r in reasons)

    def test_negative_commission_on_paid_booking(self):
        b = _booking(gross=10000, commission=-500, rate=15, net=10500)
        reasons = AnomalyDetector.check(b, {})
        assert any("Negative commission" in r for r in reasons)

    def test_net_mismatch(self):
        # gross=10000, commission=1500, net should be 8500 but is 9000
        b = _booking(gross=10000, commission=1500, rate=15, net=9000)
        reasons = AnomalyDetector.check(b, {})
        assert any("mismatch" in r for r in reasons)

    def test_no_expected_rate_configured(self):
        # No expected rate → no rate deviation check → no anomaly
        b = _booking(gross=10000, commission=1500, rate=15, net=8500)
        reasons = AnomalyDetector.check(b, {})
        assert reasons == []
