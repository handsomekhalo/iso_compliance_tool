"""
/api/reconcile/<id>/export/?format=csv|pdf

Drop this view into compliance_management/api/views.py
Then wire the URL in compliance_management/api/urls.py (see bottom of file).

Dependencies (add to requirements.txt if not present):
    reportlab>=4.0
"""

import csv
import io
import json
from datetime import datetime

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

# reportlab imports — pure Python, Railway-safe, no wkhtmltopdf needed
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from compliance_management.models import ISOReconciliationLog
from compliance_management.decorators import IsAnalystOrAbove  # your existing DRF permission


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_log_or_404(log_id, request):
    """
    Fetch the log, scoped to the requesting user's bank unless they are
    a super_admin (handled by IsSameBankOrSuperAdmin pattern).
    Returns (log, error_response) — one of them will be None.
    """
    try:
        log = ISOReconciliationLog.objects.select_related("bank", "iso_profile").get(pk=log_id)
    except ISOReconciliationLog.DoesNotExist:
        return None, Response({"error": "Reconciliation log not found."}, status=status.HTTP_404_NOT_FOUND)

    # Bank scoping: analyst/auditor can only export their own bank's logs
    user = request.user
    try:
        role = user.userrole  # OneToOne set by your UserRole model
        is_super = role.role == "super_admin"
    except AttributeError:
        is_super = False

    if not is_super and hasattr(user, "userrole"):
        user_bank = getattr(user.userrole, "bank", None)
        if user_bank and log.bank_id != user_bank.id:
            return None, Response(
                {"error": "You do not have permission to export this log."},
                status=status.HTTP_403_FORBIDDEN
            )

    return log, None


def _flatten_result_json(result_json):
    """
    Normalise result_json into a flat list of row dicts for export.

    result_json shapes we handle:
      1. List of dicts  →  use directly
      2. Dict with a key containing a list  →  use that list
      3. Dict with scalar k/v pairs  →  wrap as single-row list
      4. Anything else  →  empty list with a warning row
    """
    if isinstance(result_json, list):
        return result_json

    if isinstance(result_json, dict):
        # Check for a nested list (e.g. {"transactions": [...], "summary": {...}})
        list_keys = [k for k, v in result_json.items() if isinstance(v, list)]
        if list_keys:
            rows = result_json[list_keys[0]]
            return rows if rows else [result_json]  # fall back to summary dict if list empty
        # Scalar dict — single summary row
        return [result_json]

    return [{"warning": "result_json is empty or malformed"}]


def _all_columns(rows):
    """Union of all keys across all rows, preserving first-seen order."""
    seen = {}
    for row in rows:
        if isinstance(row, dict):
            for k in row.keys():
                seen[k] = None
    return list(seen.keys())


# ─────────────────────────────────────────────────────────────────────────────
# CSV export
# ─────────────────────────────────────────────────────────────────────────────

def _build_csv(log):
    result_json = log.result_json
    if isinstance(result_json, str):
        try:
            result_json = json.loads(result_json)
        except json.JSONDecodeError:
            result_json = {"raw": result_json}

    rows = _flatten_result_json(result_json)
    columns = _all_columns(rows)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")

    # ── metadata header block ──────────────────────────────────────────────
    meta_writer = csv.writer(output)
    meta_writer.writerow(["RandRail — RaaS Reconciliation Export"])
    meta_writer.writerow(["Log ID", log.pk])
    meta_writer.writerow(["Bank", getattr(log.bank, "name", "—")])
    meta_writer.writerow(["ISO Profile", getattr(log.iso_profile, "name", "—") if log.iso_profile else "—"])
    meta_writer.writerow(["Created", log.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if hasattr(log, "created_at") else "—"])
    meta_writer.writerow(["Status", getattr(log, "status", "—")])
    meta_writer.writerow([])  # blank separator

    # ── data rows ─────────────────────────────────────────────────────────
    writer.writeheader()
    for row in rows:
        if isinstance(row, dict):
            # Flatten nested dicts/lists to strings so CSV stays flat
            flat = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in row.items()}
            writer.writerow(flat)
        else:
            meta_writer.writerow([str(row)])

    return output.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# PDF export
# ─────────────────────────────────────────────────────────────────────────────

# Brand colours (RandRail palette — adjust hex values to match your brand)
BRAND_DARK   = colors.HexColor("#0D1B2A")   # deep navy
BRAND_ACCENT = colors.HexColor("#E8A838")   # amber / gold
BRAND_LIGHT  = colors.HexColor("#F4F6F9")   # off-white background stripe
BRAND_MUTED  = colors.HexColor("#6B7280")   # subtle text


def _build_pdf(log):
    result_json = log.result_json
    if isinstance(result_json, str):
        try:
            result_json = json.loads(result_json)
        except json.JSONDecodeError:
            result_json = {"raw": result_json}

    rows = _flatten_result_json(result_json)
    columns = _all_columns(rows)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        title=f"RandRail Reconciliation #{log.pk}",
        author="RandRail RaaS",
    )

    styles = getSampleStyleSheet()
    style_title = ParagraphStyle(
        "RRTitle",
        parent=styles["Title"],
        fontSize=18,
        textColor=BRAND_DARK,
        spaceAfter=4,
        alignment=TA_LEFT,
    )
    style_subtitle = ParagraphStyle(
        "RRSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=BRAND_MUTED,
        spaceAfter=2,
        alignment=TA_LEFT,
    )
    style_section = ParagraphStyle(
        "RRSection",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=BRAND_DARK,
        spaceBefore=12,
        spaceAfter=4,
        borderPad=2,
    )
    style_cell = ParagraphStyle(
        "RRCell",
        parent=styles["Normal"],
        fontSize=7.5,
        leading=10,
        textColor=BRAND_DARK,
    )
    style_header_cell = ParagraphStyle(
        "RRHeaderCell",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    story = []

    # ── Page header ────────────────────────────────────────────────────────
    story.append(Paragraph("RandRail — RaaS", style_title))
    story.append(Paragraph("Reconciliation Export Report", style_subtitle))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_ACCENT, spaceAfter=8))

    # ── Metadata block ─────────────────────────────────────────────────────
    story.append(Paragraph("Report Metadata", style_section))

    bank_name     = getattr(log.bank, "name", "—")
    profile_name  = getattr(log.iso_profile, "name", "—") if log.iso_profile else "—"
    created_str   = log.created_at.strftime("%d %B %Y, %H:%M UTC") if hasattr(log, "created_at") else "—"
    log_status    = str(getattr(log, "status", "—")).upper()
    xrpl_hash     = str(getattr(log, "xrpl_hash", None) or "Not yet hashed")

    meta_data = [
        ["Log ID",       str(log.pk)],
        ["Bank",         bank_name],
        ["ISO Profile",  profile_name],
        ["Created",      created_str],
        ["Status",       log_status],
        ["XRPL Hash",    xrpl_hash],
    ]

    meta_table = Table(meta_data, colWidths=[3.5 * cm, None])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR",   (0, 0), (0, -1), BRAND_DARK),
        ("TEXTCOLOR",   (1, 0), (1, -1), BRAND_MUTED),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, BRAND_LIGHT]),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("BOX",         (0, 0), (-1, -1), 0.5, BRAND_MUTED),
        ("LINEBELOW",   (0, 0), (-1, -2), 0.25, colors.HexColor("#E5E7EB")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Data table ─────────────────────────────────────────────────────────
    if rows and columns:
        story.append(Paragraph("Reconciliation Results", style_section))

        # Truncate columns for readability — show first 10 if there are many
        MAX_COLS = 10
        display_columns = columns[:MAX_COLS]
        truncated = len(columns) > MAX_COLS

        # Build header row
        header_row = [
            Paragraph(str(col).replace("_", " ").title(), style_header_cell)
            for col in display_columns
        ]
        table_data = [header_row]

        # Build data rows (cap at 500 rows in PDF for sanity)
        MAX_ROWS = 500
        for row in rows[:MAX_ROWS]:
            if isinstance(row, dict):
                cells = []
                for col in display_columns:
                    val = row.get(col, "")
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val, ensure_ascii=False)
                    cells.append(Paragraph(str(val), style_cell))
                table_data.append(cells)

        # Auto column width
        available_width = A4[0] - 3 * cm  # page width minus margins
        col_width = available_width / len(display_columns)

        data_table = Table(
            table_data,
            colWidths=[col_width] * len(display_columns),
            repeatRows=1,
        )
        data_table.setStyle(TableStyle([
            # Header row styling
            ("BACKGROUND",  (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            # Data row alternating backgrounds
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRAND_LIGHT]),
            # Grid
            ("GRID",        (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
            ("LINEBELOW",   (0, 0), (-1, 0), 1, BRAND_ACCENT),
            # Padding
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            # Alignment
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(data_table)

        if truncated:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(
                f"⚠ Showing first {MAX_COLS} of {len(columns)} columns. "
                "Use the CSV export for the full dataset.",
                style_subtitle
            ))
        if len(rows) > MAX_ROWS:
            story.append(Paragraph(
                f"⚠ Showing first {MAX_ROWS} of {len(rows)} rows. "
                "Use the CSV export for the full dataset.",
                style_subtitle
            ))
    else:
        story.append(Paragraph("No result data available for this log.", styles["Normal"]))

    # ── Footer note ────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.6 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BRAND_MUTED))
    story.append(Paragraph(
        f"Generated by RandRail RaaS on {datetime.utcnow().strftime('%d %B %Y at %H:%M UTC')}. "
        "This document is for authorised use only. "
        "Confidential — subject to POPIA and FIC Act obligations.",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=7, textColor=BRAND_MUTED, spaceBefore=4)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


