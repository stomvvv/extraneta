"""
Seed script — inserts demo user, hotel, and 23 Yandex bookings.
Idempotent: safe to run multiple times.

Usage:
    DATABASE_URL=postgresql+asyncpg://... python3 seed.py
"""
import asyncio
import os
import uuid
from decimal import Decimal
from datetime import date

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text

# ── resolve DATABASE_URL ────────────────────────────────────────────────────
def _db_url() -> str:
    url = (
        os.getenv("DATABASE_URL")
        or os.getenv("DATABASE_PRIVATE_URL")
        or os.getenv("POSTGRESQL_URL")
        or ""
    )
    for prefix, replacement in [
        ("postgresql://", "postgresql+asyncpg://"),
        ("postgres://",   "postgresql+asyncpg://"),
    ]:
        if url.startswith(prefix):
            return url.replace(prefix, replacement, 1)
    if not url:
        raise RuntimeError("Set DATABASE_URL env var before running seed.py")
    return url

DATABASE_URL = _db_url()

# ── import app models (must be on PYTHONPATH) ───────────────────────────────
from app.core.database import Base  # noqa: E402
import app.models  # noqa: F401, E402 — registers all models
from app.models.user import User, UserRole
from app.models.hotel import Hotel, HotelMember
from app.models.booking import Booking

DEMO_EMAIL   = "demo@extraneta.ru"
HOTEL_ID     = uuid.UUID("8c74c8c9-10e6-4bf9-ad79-54a0ac83a833")
HOTEL_NAME   = "Тестовый Отель"
DEMO_USER_ID = uuid.UUID("05870daf-77d7-4a69-adee-0be7c6c32c8d")

# ── booking data ────────────────────────────────────────────────────────────
BOOKINGS = [
    ("YA-1026-6263-5731", "ольга емельянова",     date(2024,12,30), date(2025,1,1),  2, 5616,  15, "paid",     "confirmed"),
    ("YA-3776-7827-1554", "Серафима Корякина",    date(2024,12,30), date(2025,1,3),  4, 31248, 15, "paid",     "confirmed"),
    ("YA-0920-7219-9819", "Екатерина Погодина",   date(2024,12,31), date(2025,1,2),  2, 19530, 15, "paid",     "confirmed"),
    ("YA-4456-1726-4936", "Роман Багаутдинов",    date(2024,12,31), date(2025,1,2),  2, 15624, 15, "paid",     "confirmed"),
    ("YA-8901-4829-1381", "Денис Дубинский",      date(2024,12,31), date(2025,1,2),  2, 28644, 15, "paid",     "confirmed"),
    ("YA-4671-0125-4079", "Тимур Цзинь",          date(2024,12,31), date(2025,1,3),  3, 8424,  15, "paid",     "confirmed"),
    ("YA-6442-5515-5535", "Мадина Адигамова",     date(2025,1,2),   date(2025,1,3),  1, 1404,  15, "paid",     "confirmed"),
    ("YA-9639-5402-3454", "Валентина Лазарева",   date(2025,1,2),   date(2025,1,3),  1, 4680,  15, "paid",     "confirmed"),
    ("YA-2839-0527-8988", "Владимир Измайлов",    date(2025,1,2),   date(2025,1,4),  2, 11718, 15, "paid",     "confirmed"),
    ("YA-4804-8526-2251", "Сергей Слепенькин",    date(2025,1,3),   date(2025,1,6),  3, 8424,  15, "paid",     "confirmed"),
    ("YA-2161-2550-5641", "Анастасия Пальчикова", date(2025,1,3),   date(2025,1,5),  2, 5616,  15, "paid",     "confirmed"),
    ("YA-4978-8383-3865", "Елизавета Измайлова",  date(2025,1,3),   date(2025,1,5),  2, 9360,  15, "paid",     "confirmed"),
    ("YA-2021-9330-2528", "Лариса Тихонова",      date(2025,1,4),   date(2025,1,6),  2, 15624, 15, "paid",     "confirmed"),
    ("YA-9970-1146-4375", "Денис Савченко",       date(2025,1,4),   date(2025,1,5),  1, 7812,  15, "paid",     "confirmed"),
    ("YA-6986-7834-2260", "Юлия Федотова",        date(2025,1,4),   date(2025,1,5),  1, 7812,  15, "paid",     "confirmed"),
    ("YA-0075-7760-1963", "Евгений Ладыгин",      date(2025,1,4),   date(2025,1,5),  1, 2808,  15, "paid",     "confirmed"),
    ("YA-0579-2896-4276", "Альберт Якупов",       date(2025,1,4),   date(2025,1,6),  2, 15624, 15, "paid",     "confirmed"),
    ("YA-0042-0955-5133", "Виктория Хагеман",     date(2025,1,4),   date(2025,1,6),  2, 15624, 15, "paid",     "confirmed"),
    ("YA-1111-2222-3333", "Иванов Иван",          date(2026,5,10),  date(2026,5,13), 3, 12000, 15, "paid",     "confirmed"),
    ("YA-2222-3333-4444", "Петрова Мария",        date(2026,5,12),  date(2026,5,15), 3, 9000,  15, "paid",     "confirmed"),
    ("YA-3333-4444-5555", "Сидоров Алексей",      date(2026,5,15),  date(2026,5,18), 3, -6000, 15, "refunded", "cancelled"),
    ("YA-4444-5555-6666", "Козлова Анна",         date(2026,5,20),  date(2026,5,23), 3, 15000, 15, "paid",     "confirmed"),
    ("YA-5555-6666-7777", "Новиков Дмитрий",      date(2026,5,25),  date(2026,5,28), 3, 8500,  15, "paid",     "confirmed"),
]


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # ── demo user ───────────────────────────────────────────────────────
        result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()
        if not user:
            import bcrypt
            hashed = bcrypt.hashpw(b"demo1234", bcrypt.gensalt()).decode()
            user = User(
                id=DEMO_USER_ID,
                email=DEMO_EMAIL,
                hashed_password=hashed,
                full_name="Demo User",
                is_active=True,
                is_verified=True,
            )
            session.add(user)
            await session.flush()
            print(f"  created user {DEMO_EMAIL}")
        else:
            user.id = DEMO_USER_ID  # ensure ID matches for FK
            print(f"  user {DEMO_EMAIL} already exists")

        # ── hotel ───────────────────────────────────────────────────────────
        result = await session.execute(select(Hotel).where(Hotel.id == HOTEL_ID))
        hotel = result.scalar_one_or_none()
        if not hotel:
            hotel = Hotel(id=HOTEL_ID, name=HOTEL_NAME)
            session.add(hotel)
            await session.flush()
            print(f"  created hotel '{HOTEL_NAME}'")
        else:
            print(f"  hotel '{HOTEL_NAME}' already exists")

        # ── hotel member ────────────────────────────────────────────────────
        result = await session.execute(
            select(HotelMember).where(
                HotelMember.hotel_id == HOTEL_ID,
                HotelMember.user_id == user.id,
            )
        )
        if not result.scalar_one_or_none():
            session.add(HotelMember(hotel_id=HOTEL_ID, user_id=user.id, role=UserRole.owner))
            print("  created hotel membership")

        # ── bookings ─────────────────────────────────────────────────────
        inserted = 0
        for (ota_id, guest, check_in, check_out, nights,
             gross, rate_pct, pay_status, book_status) in BOOKINGS:
            result = await session.execute(
                select(Booking).where(
                    Booking.hotel_id == HOTEL_ID,
                    Booking.booking_id_ota == ota_id,
                )
            )
            if result.scalar_one_or_none():
                continue
            gross_d = Decimal(str(gross))
            rate_d  = Decimal(str(rate_pct)) / 100
            commission = (gross_d * rate_d).quantize(Decimal("0.01"))
            net = gross_d - commission
            session.add(Booking(
                hotel_id=HOTEL_ID,
                source_ota="yandex",
                booking_id_ota=ota_id,
                guest_name=guest,
                check_in=check_in,
                check_out=check_out,
                nights=nights,
                gross_amount=gross_d,
                ota_commission_rate=rate_d,
                ota_commission_amount=commission,
                net_amount=net,
                currency="RUB",
                payment_status=pay_status,
                booking_status=book_status,
                is_anomaly=(gross < 0),
            ))
            inserted += 1

        await session.commit()
        print(f"  inserted {inserted} new bookings (skipped {len(BOOKINGS) - inserted} existing)")

    await engine.dispose()
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
