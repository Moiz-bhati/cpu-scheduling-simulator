"""
PDF Report Generator using ReportLab
Generates a comprehensive scheduling report.
"""

import io
import os
from typing import List, Optional
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable, Image
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from models.process import Process


def generate_pdf_report(
    processes: List[Process],
    algorithm: str,
    gantt: List[dict],
    metrics: dict,
    comparison: Optional[dict],
    output_path: str,
    gantt_image_path: Optional[str] = None,
) -> bool:
    if not REPORTLAB_AVAILABLE:
        print("reportlab not installed. Cannot generate PDF.")
        return False

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#2C3E50"),
        spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#2980B9"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = styles["BodyText"]

    story = []

    # Title
    story.append(Paragraph("CPU Scheduling Visualizer Pro", title_style))
    story.append(Paragraph("Simulation Report", heading_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Paragraph(f"Algorithm: <b>{algorithm}</b>", body_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2980B9")))
    story.append(Spacer(1, 0.3*cm))

    # Process table
    story.append(Paragraph("Process Details", heading_style))
    proc_data = [["PID", "Arrival", "Burst", "Priority", "Completion", "Waiting", "Turnaround", "Response"]]
    for p in processes:
        proc_data.append([
            p.pid,
            str(p.arrival_time),
            str(p.burst_time),
            str(p.priority),
            str(p.completion_time or "-"),
            str(p.waiting_time or "-"),
            str(p.turnaround_time or "-"),
            str(p.response_time or "-"),
        ])

    t = Table(proc_data, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2980B9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ECF0F1"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    # Gantt chart image
    if gantt_image_path and os.path.exists(gantt_image_path):
        story.append(Paragraph("Gantt Chart", heading_style))
        img = Image(gantt_image_path, width=16*cm, height=5*cm)
        story.append(img)
        story.append(Spacer(1, 0.5*cm))

    # Metrics
    story.append(Paragraph("Performance Metrics", heading_style))
    metrics_data = [
        ["Metric", "Value"],
        ["Average Waiting Time", f"{metrics.get('avg_waiting_time', 0):.2f}"],
        ["Average Turnaround Time", f"{metrics.get('avg_turnaround_time', 0):.2f}"],
        ["Average Response Time", f"{metrics.get('avg_response_time', 0):.2f}"],
        ["CPU Utilization", f"{metrics.get('cpu_utilization', 0):.1f}%"],
        ["Throughput", f"{metrics.get('throughput', 0):.4f} proc/unit"],
    ]
    mt = Table(metrics_data, hAlign="LEFT", colWidths=[8*cm, 5*cm])
    mt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#27AE60")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ECF0F1"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(mt)

    # Comparison
    if comparison:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Algorithm Comparison", heading_style))
        comp_data = [["Algorithm", "Avg WT", "Avg TAT", "Avg RT", "CPU Util %"]]
        for algo, m in comparison.items():
            comp_data.append([
                algo,
                f"{m.get('avg_waiting_time', 0):.2f}",
                f"{m.get('avg_turnaround_time', 0):.2f}",
                f"{m.get('avg_response_time', 0):.2f}",
                f"{m.get('cpu_utilization', 0):.1f}%",
            ])

        # Highlight best (lowest avg WT)
        best_algo = min(comparison.items(), key=lambda x: x[1].get("avg_waiting_time", 9999))[0]
        ct = Table(comp_data, hAlign="LEFT")
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8E44AD")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ECF0F1"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ct)
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"✓ Best Algorithm (lowest avg waiting time): <b>{best_algo}</b>", body_style))

    doc.build(story)
    return True
