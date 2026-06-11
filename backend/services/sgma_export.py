"""SGMA groundwater-use report builders (CSV + PDF) for GSA submission.

Layout follows the common GSA semi-annual extraction-report shape: monthly
extraction volumes in gallons and acre-feet plus reporter info. Kings/Kaweah
GSAs publish their own templates — before pilot submission, diff this output
against the partner GSA's current form and adjust column names/order here.
"""
import calendar
import csv
import io
from datetime import date
from decimal import Decimal
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

from backend import models

# USGS standard conversion
GALLONS_PER_ACRE_FOOT = Decimal("325851")

CSV_HEADER = "month,extraction_gallons,extraction_acre_feet"


def _acre_feet(gallons: Decimal) -> Decimal:
    return round(gallons / GALLONS_PER_ACRE_FOOT, 4)


def _formula_safe(value: str) -> str:
    """Neutralize spreadsheet formula injection (CWE-1236). Excel/Sheets
    execute cells starting with = + - @ when the CSV is opened — and this
    file's audience is a GSA office, so user-controlled text must not
    become a live formula on their machine."""
    if value and value[0] in "=+-@\t\r":
        return "'" + value
    return value


def monthly_rows(monthly_gallons: dict[int, Decimal]) -> list[tuple[str, Decimal, Decimal]]:
    return [
        (
            calendar.month_name[m],
            monthly_gallons.get(m, Decimal("0")),
            _acre_feet(monthly_gallons.get(m, Decimal("0"))),
        )
        for m in range(1, 13)
    ]


def build_csv(farm: models.Farm, year: int, monthly_gallons: dict[int, Decimal]) -> str:
    # csv.writer quotes embedded commas/newlines so a crafted farm name
    # can't inject rows; _formula_safe defuses leading formula characters.
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([f"# SGMA Groundwater Extraction Report — {year}"])
    writer.writerow([f"# Farm: {_formula_safe(farm.name)}"])
    writer.writerow([f"# Water source: {farm.water_source.value if farm.water_source else 'unreported'}"])
    writer.writerow([f"# Acreage: {farm.acreage_acres if farm.acreage_acres is not None else 'unreported'}"])
    writer.writerow([f"# Generated: {date.today().isoformat()} by AquaAlert from farmer-logged irrigation events"])
    writer.writerow(CSV_HEADER.split(","))
    total = Decimal("0")
    for month, gallons, acre_feet in monthly_rows(monthly_gallons):
        total += gallons
        writer.writerow([month, gallons, acre_feet])
    writer.writerow(["TOTAL", total, _acre_feet(total)])
    return buffer.getvalue()


def build_pdf(farm: models.Farm, year: int, monthly_gallons: dict[int, Decimal]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"SGMA Report {year} — {farm.name}")
    styles = getSampleStyleSheet()

    rows = monthly_rows(monthly_gallons)
    total = sum((g for _, g, _ in rows), Decimal("0"))
    table_data = [["Month", "Extraction (gallons)", "Extraction (acre-feet)"]]
    table_data += [[m, f"{g:,}", f"{af}"] for m, g, af in rows]
    table_data.append(["TOTAL", f"{total:,}", f"{_acre_feet(total)}"])

    table = Table(table_data, colWidths=[1.8 * inch, 2.2 * inch, 2.2 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#166534")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    ]))

    source = farm.water_source.value if farm.water_source else "unreported"
    acreage = f"{farm.acreage_acres} acres" if farm.acreage_acres is not None else "unreported"
    doc.build([
        Paragraph(f"SGMA Groundwater Extraction Report — {year}", styles["Title"]),
        # Paragraph parses XML-ish markup — unescaped user text can inject
        # tags or crash the build on malformed ones.
        Paragraph(f"Farm: {escape(farm.name)}", styles["Normal"]),
        Paragraph(f"Water source: {source} · Acreage: {acreage}", styles["Normal"]),
        Paragraph(
            f"Generated {date.today().isoformat()} by AquaAlert from farmer-logged irrigation events.",
            styles["Normal"],
        ),
        Spacer(1, 0.3 * inch),
        table,
    ])
    return buffer.getvalue()
