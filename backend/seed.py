"""
Seed script — inserts demo hotel with 7 OTA × 5+ bookings.
Idempotent: safe to run multiple times.

Usage:
    cd backend && python seed.py
"""
import os
import sys
import random
from decimal import Decimal
from datetime import date, timedelta

# Add backend dir to path
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base  # noqa: E402
import models  # noqa: F401, E402
from models.hotel import Hotel
from models.booking import Booking
from models.commission_setting import CommissionSetting

HOTEL_NAME = "Гостиница Центральная"

OTA_RATES = {
    "yandex": 18.0,
    "ostrovok": 15.0,
    "bronevic": 12.0,
    "tinkoff": 20.0,
    "2gis": 10.0,
    "101hotel": 15.0,
    "academservis": 12.0,
}

GUESTS = [
    "Иванов Иван", "Петрова Мария", "Сидоров Алексей", "Козлова Анна",
    "Новиков Дмитрий", "Морозова Елена", "Волков Андрей", "Соколова Наталья",
    "Лебедев Сергей", "Попова Ольга", "Кузнецов Игорь", "Зайцева Татьяна",
    "Медведев Павел", "Степанова Юлия", "Орлов Виктор",
]


def make_bookings(hotel_id: int) -> list[Booking]:
    today = date.today()
    bookings = []
    anomaly_count = 0

    for ota, expected_rate in OTA_RATES.items():
        for i in range(6):  # 6 bookings per OTA
            check_in = today - timedelta(days=random.randint(10, 180))
            nights = random.randint(1, 5)
            check_out = check_in + timedelta(days=nights)
            gross = Decimal(str(random.randint(3000, 25000)))

            # Determine status
            r = random.random()
            if r < 0.70:
                status = "confirmed"
            elif r < 0.90:
                status = "cancelled"
            else:
                status = "no_show"

            # Commission rate (sometimes anomalous)
            if anomaly_count < 2 and i == 4:
                # Anomaly: wrong commission rate
                rate = Decimal(str(expected_rate + 5.0))
                anomaly_count += 1
            elif anomaly_count < 3 and status == "cancelled" and i == 5:
                # Anomaly: cancelled but commission not returned
                rate = Decimal(str(expected_rate))
                anomaly_count += 1
            else:
                rate = Decimal(str(expected_rate))

            commission = (gross * rate / Decimal("100")).quantize(Decimal("0.01"))
            net = gross - commission

            has_anomaly = False
            anomaly_reason = ""
            if abs(float(rate) - expected_rate) > 1.0:
                has_anomaly = True
                anomaly_reason = f"Комиссия {rate}% ≠ ожидаемой {expected_rate}%"
            if status == "cancelled" and float(commission) > 0 and not anomaly_reason:
                has_anomaly = True
                anomaly_reason = "Отменённая бронь, но комиссия не возвращена"

            bookings.append(Booking(
                hotel_id=hotel_id,
                source_ota=ota,
                booking_id_ota=f"{ota.upper()}-SEED-{i+1:03d}-{hotel_id}",
                guest_name=random.choice(GUESTS),
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                gross_amount=gross,
                ota_commission_rate=rate,
                ota_commission_amount=commission,
                net_amount=net,
                booking_status=status,
                payment_status="paid" if status != "cancelled" else "refunded",
                has_anomaly=has_anomaly,
                anomaly_reason=anomaly_reason,
                raw_row={},
            ))

    return bookings


def seed():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Hotel
        hotel = db.query(Hotel).filter(Hotel.name == HOTEL_NAME).first()
        if not hotel:
            hotel = Hotel(name=HOTEL_NAME, address="г. Москва, ул. Центральная, 1")
            db.add(hotel)
            db.flush()
            print(f"  Created hotel '{HOTEL_NAME}' (id={hotel.id})")
        else:
            print(f"  Hotel '{HOTEL_NAME}' already exists (id={hotel.id})")

        # Commission settings
        existing_cs = db.query(CommissionSetting).filter(
            CommissionSetting.hotel_id == hotel.id
        ).count()
        if existing_cs == 0:
            for ota, rate in OTA_RATES.items():
                db.add(CommissionSetting(hotel_id=hotel.id, ota=ota, expected_rate=rate))
            print("  Created commission settings for all OTAs")

        # Bookings — skip if already seeded
        existing = db.query(Booking).filter(
            Booking.hotel_id == hotel.id,
            Booking.booking_id_ota.like("%-SEED-%"),
        ).count()
        if existing > 0:
            print(f"  Seed bookings already exist ({existing}), skipping")
        else:
            bookings = make_bookings(hotel.id)
            for b in bookings:
                db.add(b)
            print(f"  Inserted {len(bookings)} seed bookings ({len(OTA_RATES)} OTAs × 6)")

        db.commit()
        print("Seed complete.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
