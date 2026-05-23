"""
Export service — generates Excel (.xlsx) and PDF reports.
"""

import io
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus, PaymentStatus
from app.models.hotel import Hotel
from app.schemas.analytics import SummaryMetrics, ChannelMetrics
from app.services.analytics import AnalyticsService


def _fmt_rub(value: Decimal) -> str:
    return f"{value:,.2f} ₽".replace(",", " ")


async def export_excel(
    db: AsyncSession,
    hotel_id: UUID,
    date_from: date,
    date_to: date,
) -> bytes:
    import xlsxwriter

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})

    # Formats
    title_fmt = wb.add_format({"bold": True, "font_size": 14, "font_name": "Arial"})
    header_fmt = wb.add_format({"bold": True, "bg_color": "#1E3A5F", "font_color": "white",
                                "font_name": "Arial", "border": 1})
    money_fmt = wb.add_format({"num_format": '# ##0.00 ₽', "font_name": "Arial"})
    pct_fmt = wb.add_format({"num_format": "0.00%", "font_name": "Arial"})
    date_fmt = wb.add_format({"num_format": "dd.mm.yyyy", "font_name": "Arial"})
    cell_fmt = wb.add_format({"font_name": "Arial"})
    red_fmt = wb.add_format({"font_color": "red", "font_name": "Arial"})

    hotel_result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
    hotel = hotel_result.scalar_one_or_none()
    hotel_name = hotel.name if hotel else str(hotel_id)

    summary = await AnalyticsService.get_summary(db, hotel_id, date_from, date_to)
    channels = await AnalyticsService.get_channels(db, hotel_id, date_from, date_to)

    # ── Sheet 1: Summary ─────────────────────────────────────────────────────
    ws1 = wb.add_worksheet("Сводка")
    ws1.set_column("A:A", 35)
    ws1.set_column("B:B", 20)
    ws1.write("A1", f"Отчёт: {hotel_name}", title_fmt)
    ws1.write("A2", f"Период: {date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}", cell_fmt)
    ws1.write("A4", "Показатель", header_fmt)
    ws1.write("B4", "Значение", header_fmt)

    metrics = [
        ("Валовая выручка", float(summary.gross_revenue), money_fmt),
        ("Комиссии OTA", float(summary.total_commission), money_fmt),
        ("Чистая выручка", float(summary.net_revenue), money_fmt),
        ("Средний % комиссии", float(summary.commission_rate_pct) / 100, pct_fmt),
        ("Всего броней", summary.total_bookings, cell_fmt),
        ("Подтверждённых", summary.confirmed_bookings, cell_fmt),
        ("Отменённых", summary.cancelled_bookings, cell_fmt),
        ("Средний чек", float(summary.avg_booking_value), money_fmt),
    ]
    for i, (label, val, fmt) in enumerate(metrics, start=5):
        ws1.write(f"A{i}", label, cell_fmt)
        ws1.write(f"B{i}", val, fmt)

    # ── Sheet 2: Channels ────────────────────────────────────────────────────
    ws2 = wb.add_worksheet("По каналам")
    ch_headers = ["OTA", "Броней", "Валовая выручка", "Комиссия", "% комиссии", "Чистая выручка", "Доля канала", "Средний чек"]
    col_widths = [15, 10, 20, 20, 14, 20, 14, 18]
    for ci, (h, w) in enumerate(zip(ch_headers, col_widths)):
        ws2.set_column(ci, ci, w)
        ws2.write(0, ci, h, header_fmt)

    for ri, ch in enumerate(channels, start=1):
        ws2.write(ri, 0, ch.source_ota, cell_fmt)
        ws2.write(ri, 1, ch.bookings_count, cell_fmt)
        ws2.write(ri, 2, float(ch.gross_revenue), money_fmt)
        ws2.write(ri, 3, float(ch.commission_amount), money_fmt)
        ws2.write(ri, 4, float(ch.commission_rate_pct) / 100, pct_fmt)
        ws2.write(ri, 5, float(ch.net_revenue), money_fmt)
        ws2.write(ri, 6, float(ch.channel_share_pct) / 100, pct_fmt)
        ws2.write(ri, 7, float(ch.avg_booking_value), money_fmt)

    # ── Sheet 3: All bookings ─────────────────────────────────────────────────
    ws3 = wb.add_worksheet("Бронирования")
    b_headers = ["OTA", "ID брони", "Гость", "Тип номера", "Заезд", "Выезд",
                 "Ночей", "Сумма гостя", "Комиссия", "% комиссии", "Чистая сумма",
                 "Статус оплаты", "Статус брони", "Аномалия"]
    b_widths = [12, 22, 25, 18, 12, 12, 8, 16, 14, 12, 16, 14, 14, 8]
    for ci, (h, w) in enumerate(zip(b_headers, b_widths)):
        ws3.set_column(ci, ci, w)
        ws3.write(0, ci, h, header_fmt)

    bookings_result = await db.execute(
        select(Booking)
        .where(
            Booking.hotel_id == hotel_id,
            Booking.check_in >= date_from,
            Booking.check_in <= date_to,
        )
        .order_by(Booking.check_in.desc())
    )
    bookings = bookings_result.scalars().all()

    for ri, b in enumerate(bookings, start=1):
        row_fmt = red_fmt if b.is_anomaly else cell_fmt
        ws3.write(ri, 0, b.source_ota.value, row_fmt)
        ws3.write(ri, 1, b.booking_id_ota, row_fmt)
        ws3.write(ri, 2, b.guest_name, row_fmt)
        ws3.write(ri, 3, b.room_type or "", row_fmt)
        ws3.write_datetime(ri, 4, b.check_in, date_fmt) if b.check_in else None
        ws3.write_datetime(ri, 5, b.check_out, date_fmt) if b.check_out else None
        ws3.write(ri, 6, b.nights, cell_fmt)
        ws3.write(ri, 7, float(b.gross_amount), money_fmt)
        ws3.write(ri, 8, float(b.ota_commission_amount), money_fmt)
        ws3.write(ri, 9, float(b.ota_commission_rate) / 100, pct_fmt)
        ws3.write(ri, 10, float(b.net_amount), money_fmt)
        ws3.write(ri, 11, b.payment_status.value, row_fmt)
        ws3.write(ri, 12, b.booking_status.value, row_fmt)
        ws3.write(ri, 13, "⚠" if b.is_anomaly else "", row_fmt)

    # ── Sheet 4: Anomalies ───────────────────────────────────────────────────
    ws4 = wb.add_worksheet("Аномалии")
    a_headers = ["OTA", "ID брони", "Гость", "Заезд", "Сумма гостя", "Причина аномалии"]
    a_widths = [12, 22, 25, 12, 16, 60]
    for ci, (h, w) in enumerate(zip(a_headers, a_widths)):
        ws4.set_column(ci, ci, w)
        ws4.write(0, ci, h, header_fmt)

    anomalies = [b for b in bookings if b.is_anomaly]
    for ri, b in enumerate(anomalies, start=1):
        ws4.write(ri, 0, b.source_ota.value, red_fmt)
        ws4.write(ri, 1, b.booking_id_ota, red_fmt)
        ws4.write(ri, 2, b.guest_name, red_fmt)
        ws4.write_datetime(ri, 3, b.check_in, date_fmt) if b.check_in else None
        ws4.write(ri, 4, float(b.gross_amount), money_fmt)
        ws4.write(ri, 5, b.anomaly_reasons or "", red_fmt)

    wb.close()
    return output.getvalue()


async def export_pdf(
    db: AsyncSession,
    hotel_id: UUID,
    date_from: date,
    date_to: date,
) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    hotel_result = await db.execute(select(Hotel).where(Hotel.id == hotel_id))
    hotel = hotel_result.scalar_one_or_none()
    hotel_name = hotel.name if hotel else str(hotel_id)

    summary = await AnalyticsService.get_summary(db, hotel_id, date_from, date_to)
    channels = await AnalyticsService.get_channels(db, hotel_id, date_from, date_to)

    # Top 5 bookings by gross amount
    top5_result = await db.execute(
        select(Booking)
        .where(
            Booking.hotel_id == hotel_id,
            Booking.check_in >= date_from,
            Booking.check_in <= date_to,
        )
        .order_by(Booking.gross_amount.desc())
        .limit(5)
    )
    top5 = top5_result.scalars().all()

    anomalies_result = await db.execute(
        select(Booking)
        .where(
            Booking.hotel_id == hotel_id,
            Booking.check_in >= date_from,
            Booking.check_in <= date_to,
            Booking.is_anomaly == True,
        )
        .limit(20)
    )
    anomalies = anomalies_result.scalars().all()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    navy = colors.HexColor("#1E3A5F")

    title_style = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=16, textColor=navy, spaceAfter=6)
    subtitle_style = ParagraphStyle("subtitle", fontName="Helvetica", fontSize=10, textColor=colors.grey, spaceAfter=12)
    section_style = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=12, textColor=navy,
                                   spaceBefore=16, spaceAfter=8)

    def _tbl_style(header_color=navy):
        return TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), header_color),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FA")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])

    story = []
    story.append(Paragraph(f"Управленческий отчёт — {hotel_name}", title_style))
    story.append(Paragraph(
        f"Период: {date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')} | "
        f"Сформирован: {date.today().strftime('%d.%m.%Y')}",
        subtitle_style,
    ))

    # Key metrics block
    story.append(Paragraph("Ключевые показатели", section_style))
    kpi_data = [
        ["Показатель", "Значение"],
        ["Валовая выручка", _fmt_rub(summary.gross_revenue)],
        ["Комиссии OTA", f"{_fmt_rub(summary.total_commission)} ({summary.commission_rate_pct:.1f}%)"],
        ["Чистая выручка", _fmt_rub(summary.net_revenue)],
        ["Всего броней", str(summary.total_bookings)],
        ["Средний чек", _fmt_rub(summary.avg_booking_value)],
    ]
    kpi_tbl = Table(kpi_data, colWidths=[10*cm, 7*cm])
    kpi_tbl.setStyle(_tbl_style())
    story.append(kpi_tbl)

    # Channels block
    story.append(Paragraph("Разбивка по каналам", section_style))
    ch_data = [["OTA", "Броней", "Валовая", "Комиссия", "%", "Чистая"]]
    for ch in channels:
        ch_data.append([
            ch.source_ota,
            str(ch.bookings_count),
            _fmt_rub(ch.gross_revenue),
            _fmt_rub(ch.commission_amount),
            f"{ch.commission_rate_pct:.1f}%",
            _fmt_rub(ch.net_revenue),
        ])
    ch_tbl = Table(ch_data, colWidths=[3*cm, 2*cm, 4*cm, 4*cm, 2*cm, 4*cm])
    ch_tbl.setStyle(_tbl_style())
    story.append(ch_tbl)

    # Top 5 bookings
    if top5:
        story.append(Paragraph("Топ-5 броней по стоимости", section_style))
        t5_data = [["Гость", "OTA", "Заезд", "Выезд", "Сумма гостя", "Чистая"]]
        for b in top5:
            t5_data.append([
                b.guest_name,
                b.source_ota.value,
                b.check_in.strftime("%d.%m.%Y"),
                b.check_out.strftime("%d.%m.%Y"),
                _fmt_rub(b.gross_amount),
                _fmt_rub(b.net_amount),
            ])
        t5_tbl = Table(t5_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 4*cm, 4*cm])
        t5_tbl.setStyle(_tbl_style())
        story.append(t5_tbl)

    # Anomalies
    if anomalies:
        story.append(Paragraph(f"Аномалии ({len(anomalies)})", section_style))
        an_data = [["ID брони", "OTA", "Гость", "Сумма", "Причина"]]
        for b in anomalies:
            an_data.append([
                b.booking_id_ota,
                b.source_ota.value,
                b.guest_name,
                _fmt_rub(b.gross_amount),
                (b.anomaly_reasons or "")[:80],
            ])
        an_tbl = Table(an_data, colWidths=[3*cm, 2.5*cm, 4*cm, 4*cm, 6*cm])
        an_tbl.setStyle(TableStyle([
            *_tbl_style().getCommands(),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#C0392B")),
        ]))
        story.append(an_tbl)

    doc.build(story)
    return output.getvalue()
