from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
from typing import List, Dict, Any
import os


def _format_currency(value: float) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


def _format_quantity(value: float, unit: str = "kg") -> str:
    try:
        return f"{float(value):,.2f} {unit}"
    except (TypeError, ValueError):
        return f"0.00 {unit}"


def _format_percentage(value: float) -> str:
    try:
        return f"{float(value):,.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def _build_table(data: List[List[Any]], col_widths: List[float], header_bg: colors.Color) -> Table:
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_bg),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f6f8fb")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d6e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
            ]
        )
    )
    return table

def generate_pdf_report(report_data: dict, company_id: str) -> str:
    """Generate PDF report using ReportLab."""
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/waste_report_{company_id}_{timestamp}.pdf"
    
    # Create PDF document
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.85 * inch,
        bottomMargin=0.85 * inch,
    )
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    sub_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=colors.HexColor("#2c3e50"),
        spaceBefore=10,
        spaceAfter=8,
    )
    normal_small = ParagraphStyle(
        "NormalSmall",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
    )
    note_style = ParagraphStyle(
        "Note",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#6c7a89"),
        leftIndent=6,
        spaceBefore=4,
    )
    
    # Cover Section
    story.append(Paragraph("Automated Waste Financial Ledger", title_style))
    story.append(Spacer(1, 0.15 * inch))
    story.append(
        Paragraph(
            "Financial Performance Report for Waste Transactions",
            ParagraphStyle(
                "subtitle",
                parent=styles["Heading2"],
                alignment=TA_CENTER,
                fontSize=14,
                textColor=colors.HexColor("#5d6d7e"),
                spaceAfter=12,
            ),
        )
    )
    story.append(
        Paragraph(
            f"<b>Company:</b> {report_data.get('company_name', company_id)}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            f"<b>Company ID:</b> {company_id}", styles["Normal"]
        )
    )
    story.append(
        Paragraph(
            f"<b>Report Period:</b> {report_data.get('report_period', 'N/A')}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            f"<b>Generated On:</b> {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.25 * inch))
    
    # Executive Summary - Use actual revenue/costs when available
    story.append(Paragraph("Executive Summary", heading_style))
    
    # Get actual vs expected values
    total_actual_revenue = report_data.get("total_actual_revenue", 0) or report_data.get("total_revenue", 0)
    total_expected_revenue = report_data.get("total_expected_revenue", 0)
    total_actual_cost = report_data.get("total_actual_cost", 0) or report_data.get("total_cost", 0)
    total_expected_cost = report_data.get("total_expected_cost", 0)
    
    # Use actual values for display
    display_revenue = total_actual_revenue if total_actual_revenue > 0 else total_expected_revenue
    display_cost = total_actual_cost if total_actual_cost > 0 else total_expected_cost
    display_nwv = report_data.get("net_waste_value", 0)
    
    key_metrics = [
        ["Total Revenue From Recyclables", _format_currency(display_revenue)],
        ["Total Disposal & Treatment Cost", _format_currency(display_cost)],
        ["Net Waste Value (Revenue - Costs)", _format_currency(display_nwv)],
        ["Transactions Analysed", f"{report_data.get('total_transactions', 0)} entries"],
    ]
    
    # Add actual vs expected comparison if available
    if total_actual_revenue > 0 or total_actual_cost > 0:
        story.append(Spacer(1, 0.1 * inch))
        variance_note = []
        if total_actual_revenue > 0 and total_expected_revenue > 0:
            rev_variance = total_actual_revenue - total_expected_revenue
            rev_variance_pct = (rev_variance / total_expected_revenue * 100) if total_expected_revenue > 0 else 0
            variance_note.append(f"Revenue: Actual ₹{total_actual_revenue:,.2f} vs Expected ₹{total_expected_revenue:,.2f} ({rev_variance_pct:+.1f}%)")
        if total_actual_cost > 0 and total_expected_cost > 0:
            cost_variance = total_actual_cost - total_expected_cost
            cost_variance_pct = (cost_variance / total_expected_cost * 100) if total_expected_cost > 0 else 0
            variance_note.append(f"Cost: Actual ₹{total_actual_cost:,.2f} vs Expected ₹{total_expected_cost:,.2f} ({cost_variance_pct:+.1f}%)")
        
        if variance_note:
            story.append(Paragraph(
                "<b>Actual vs Expected:</b> " + " | ".join(variance_note),
                note_style
            ))
    story.append(
        _build_table(
            [["Metric", "Period Value"]] + key_metrics,
            [3.5 * inch, 2.8 * inch],
            colors.HexColor("#2980b9"),
        )
    )
    
    kpi_summary = report_data.get("kpi_summary", {})
    if kpi_summary:
        story.append(Spacer(1, 0.12 * inch))
        story.append(Paragraph("Diversion & Efficiency KPIs", sub_heading_style))
        kpi_rows = [
            ["Total Waste Processed", _format_quantity(kpi_summary.get("total_quantity_kg", 0))],
            ["Recyclable Capture", _format_quantity(kpi_summary.get("recyclable_quantity_kg", 0))],
            ["Diversion Rate", _format_percentage(kpi_summary.get("diversion_rate_percent", 0))],
            ["Hazardous Stream Share", _format_percentage(kpi_summary.get("hazardous_ratio_percent", 0))],
            ["Revenue per kg", _format_currency(kpi_summary.get("revenue_per_kg", 0))],
            ["Cost per kg", _format_currency(kpi_summary.get("cost_per_kg", 0))],
            ["Net Value per kg", _format_currency(kpi_summary.get("net_value_per_kg", 0))],
        ]
        story.append(
            _build_table(
                [["KPI", "Value"]] + kpi_rows,
                [3.2 * inch, 3.1 * inch],
                colors.HexColor("#1abc9c"),
            )
        )
    story.append(
        Paragraph(
            "This summary aggregates all recorded waste transactions for the selected period, highlighting revenue streams from recyclable commodities, disposal liabilities, and resulting net waste value (NWV).",
            normal_small,
        )
    )
    
    # Historical comparison (if available)
    historical = report_data.get("historical_comparison")
    if historical:
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Historical Comparison Insights", sub_heading_style))
        prev = historical.get("previous_period", {})
        change = historical.get("nwv_change", 0)
        change_pct = historical.get("nwv_change_percent", 0)
        hist_rows = [
            ["Previous Period (NWV)", _format_currency(prev.get("net_waste_value", 0))],
            ["Revenue Δ vs Previous Period", _format_currency(report_data.get("total_revenue", 0) - prev.get("total_revenue", 0))],
            ["Cost Δ vs Previous Period", _format_currency(report_data.get("total_cost", 0) - prev.get("total_cost", 0))],
            ["NWV Δ vs Previous Period", f"{_format_currency(change)} ({_format_percentage(change_pct)})"],
        ]
        story.append(
            _build_table(
                [["Comparison Metric", "Change"]] + hist_rows,
                [3.5 * inch, 2.8 * inch],
                colors.HexColor("#8e44ad"),
            )
        )
        period_text = f"{prev.get('start_date', '')} to {prev.get('end_date', '')}"
        story.append(Paragraph(f"Previous period window: {period_text}", note_style))
    
    story.append(Spacer(1, 0.25 * inch))
    
    # Revenue Breakdown - Use actual revenue from entries
    revenue_details = report_data.get("detailed_revenue", [])
    if revenue_details:
        story.append(Paragraph("Material-Wise Revenue Breakdown", heading_style))
        revenue_rows = [
            ["Material", "Avg Quality", "Quantity", "Effective Price/kg", "Generated Value"]
        ]
        total_revenue_detail = 0
        
        for item in revenue_details:
            item_value = item.get("value", 0) or item.get("actual_revenue", 0) or item.get("expected_revenue", 0)
            total_revenue_detail += item_value
            
            revenue_rows.append(
                [
                    item.get("material", "Unknown"),
                    _format_percentage(item.get("quality_score", 1) * 100 if item.get("quality_score") else 100),
                    _format_quantity(item.get("quantity_kg", 0)),
                    _format_currency(item.get("price_per_kg", 0)),
                    _format_currency(item_value),
                ]
            )
        
        # Add totals row
        revenue_rows.append([
            "<b>Total</b>",
            "",
            "",
            "",
            f"<b>{_format_currency(total_revenue_detail)}</b>",
        ])
        
        story.append(
            _build_table(
                revenue_rows,
                [1.6 * inch, 1.1 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch],
                colors.HexColor("#27ae60"),
            )
        )
        top_material = report_data.get("top_material")
        if top_material:
            story.append(
                Paragraph(
                    f"Top-performing material: {top_material.get('material_type', 'N/A')} with "
                    f"{_format_currency(top_material.get('net_value', 0))} net value across "
                    f"{top_material.get('transaction_count', 0)} transactions.",
                    note_style,
                )
            )
        story.append(
            Paragraph(
                "Revenue contributions are calculated using real-time or latest indexed commodity pricing adjusted by measured quality scores at the point of segregation. Values shown use actual revenue from entries when available.",
                note_style,
            )
        )
        story.append(Spacer(1, 0.2 * inch))
    
    # Cost Breakdown - Use actual costs from entries
    cost_details = report_data.get("detailed_costs", [])
    if cost_details:
        story.append(Paragraph("Disposal & Treatment Cost Breakdown", heading_style))
        cost_rows = [["Waste Stream", "Quantity", "Cost per kg", "Total Cost"]]
        total_cost_detail = 0
        
        for item in cost_details:
            item_cost = item.get("value", 0) or item.get("actual_cost", 0) or item.get("expected_cost", 0)
            total_cost_detail += item_cost
            
            cost_rows.append(
                [
                    item.get("type", "Unknown"),
                    _format_quantity(item.get("quantity_kg", 0)),
                    _format_currency(item.get("cost_per_kg", 0)),
                    _format_currency(item_cost),
                ]
            )
        
        # Add totals row
        cost_rows.append([
            "<b>Total</b>",
            "",
            "",
            f"<b>{_format_currency(total_cost_detail)}</b>",
        ])
        
        story.append(
            _build_table(
                cost_rows,
                [2.2 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch],
                colors.HexColor("#c0392b"),
            )
        )
        story.append(
            Paragraph(
                "Disposal costs include transportation, landfill tipping, hazardous handling, and regulatory compliance fees captured against each waste transaction. Values shown use actual costs from entries when available.",
                note_style,
            )
        )
        story.append(Spacer(1, 0.2 * inch))
        
        # Cost Breakdown Analysis (if available)
        cost_breakdown_analysis = report_data.get("cost_breakdown_analysis", {})
        if cost_breakdown_analysis and cost_breakdown_analysis.get("has_breakdown_data"):
            story.append(Paragraph("Cost Breakdown by Type", sub_heading_style))
            breakdown_rows = [
                ["Cost Type", "Amount", "Percentage"],
                ["Disposal", _format_currency(cost_breakdown_analysis.get("disposal_amount", 0)), _format_percentage(cost_breakdown_analysis.get("disposal_percentage", 0))],
                ["Transportation", _format_currency(cost_breakdown_analysis.get("transportation_amount", 0)), _format_percentage(cost_breakdown_analysis.get("transportation_percentage", 0))],
                ["Processing", _format_currency(cost_breakdown_analysis.get("processing_amount", 0)), _format_percentage(cost_breakdown_analysis.get("processing_percentage", 0))],
                ["Other", _format_currency(cost_breakdown_analysis.get("other_amount", 0)), _format_percentage(cost_breakdown_analysis.get("other_percentage", 0))],
            ]
            breakdown_rows.append([
                "<b>Total</b>",
                f"<b>{_format_currency(cost_breakdown_analysis.get('total_breakdown_cost', 0))}</b>",
                "<b>100.0%</b>",
            ])
            story.append(
                _build_table(
                    breakdown_rows,
                    [2.0 * inch, 2.0 * inch, 2.0 * inch],
                    colors.HexColor("#e74c3c"),
                )
            )
            story.append(Spacer(1, 0.2 * inch))
    
    # Quality & compliance metrics
    quality_metrics = report_data.get("quality_metrics", {})
    if quality_metrics:
        story.append(Paragraph("Quality & Compliance Metrics", heading_style))
        qm_rows = [
            ["Average Material Quality Score", _format_percentage(quality_metrics.get("average_quality_score", 1) * 100)],
            ["Average Contamination Level", _format_percentage(quality_metrics.get("average_contamination_level", 0) * 100)],
            ["Peak Contamination Level", _format_percentage(quality_metrics.get("max_contamination_level", 0) * 100)],
            ["Transactions below 85% Quality", str(quality_metrics.get("transactions_below_quality_threshold", 0))],
        ]
        story.append(
            _build_table(
                [["Quality Indicator", "Observed Value"]] + qm_rows,
                [3.4 * inch, 2.9 * inch],
                colors.HexColor("#9b59b6"),
            )
        )
        story.append(
            Paragraph(
                "Consistent quality scores above 85% unlock premium pricing. Elevated contamination levels drive up downstream processing and rejection costs.",
                note_style,
            )
        )
        story.append(Spacer(1, 0.2 * inch))
    
    # Material summary (all materials) - Use actual revenue/costs
    material_summary = report_data.get("material_summary", [])
    if material_summary:
        story.append(Paragraph("Material Performance Summary", heading_style))
        material_rows = [
            ["Material", "Categories", "Transactions", "Total Quantity", "Revenue", "Cost", "Net Value"]
        ]
        total_mat_revenue = 0
        total_mat_cost = 0
        total_mat_net = 0
        
        for mat in material_summary:
            mat_revenue = mat.get("total_revenue", 0)
            mat_cost = mat.get("total_cost", 0)
            mat_net = mat.get("net_value", 0)
            
            total_mat_revenue += mat_revenue
            total_mat_cost += mat_cost
            total_mat_net += mat_net
            
            material_rows.append(
                [
                    mat.get("material_type", "Unknown"),
                    ", ".join(mat.get("categories", [])) or "—",
                    str(mat.get("transaction_count", 0)),
                    _format_quantity(mat.get("total_quantity_kg", 0)),
                    _format_currency(mat_revenue),
                    _format_currency(mat_cost),
                    _format_currency(mat_net),
                ]
            )
        
        # Add totals row
        material_rows.append([
            "<b>Total</b>",
            "",
            "",
            "",
            f"<b>{_format_currency(total_mat_revenue)}</b>",
            f"<b>{_format_currency(total_mat_cost)}</b>",
            f"<b>{_format_currency(total_mat_net)}</b>",
        ])
        
        story.append(
            _build_table(
                material_rows,
                [1.3 * inch, 1.5 * inch, 1.0 * inch, 1.2 * inch, 1.2 * inch, 1.1 * inch, 1.2 * inch],
                colors.HexColor("#34495e"),
            )
        )
        
        # Add material profitability insights if available
        material_profitability = report_data.get("material_profitability", {})
        if material_profitability:
            story.append(Spacer(1, 0.1 * inch))
            story.append(Paragraph("Material Profitability Analysis", sub_heading_style))
            profit_rows = [["Material", "Profit Margin", "Revenue/kg", "Cost/kg", "Net Value/kg", "Score"]]
            for mat_type, metrics in material_profitability.items():
                profit_rows.append([
                    mat_type,
                    _format_percentage(metrics.get("profit_margin_percent", 0)),
                    _format_currency(metrics.get("revenue_per_kg", 0)),
                    _format_currency(metrics.get("cost_per_kg", 0)),
                    _format_currency(metrics.get("net_value_per_kg", 0)),
                    f"{metrics.get('profitability_score', 0):.1f}"
                ])
            story.append(
                _build_table(
                    profit_rows,
                    [1.2 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch, 0.8 * inch],
                    colors.HexColor("#3498db"),
                )
            )
        
        story.append(Spacer(1, 0.2 * inch))
    
    # Category summary - Use actual revenue/costs
    category_summary = report_data.get("category_summary", [])
    if category_summary:
        story.append(Paragraph("Category-Level Net Waste Value", sub_heading_style))
        category_rows = [["Category", "Transactions", "Total Quantity", "Revenue", "Cost", "Net Value"]]
        total_cat_revenue = 0
        total_cat_cost = 0
        total_cat_net = 0
        
        for cat in category_summary:
            cat_revenue = cat.get("total_revenue", 0)
            cat_cost = cat.get("total_cost", 0)
            cat_net = cat.get("net_value", 0)
            
            total_cat_revenue += cat_revenue
            total_cat_cost += cat_cost
            total_cat_net += cat_net
            
            category_rows.append(
                [
                    cat.get("category", "Unknown").title(),
                    str(cat.get("transaction_count", 0)),
                    _format_quantity(cat.get("total_quantity_kg", 0)),
                    _format_currency(cat_revenue),
                    _format_currency(cat_cost),
                    _format_currency(cat_net),
                ]
            )
        
        # Add totals row
        category_rows.append([
            "<b>Total</b>",
            "",
            "",
            f"<b>{_format_currency(total_cat_revenue)}</b>",
            f"<b>{_format_currency(total_cat_cost)}</b>",
            f"<b>{_format_currency(total_cat_net)}</b>",
        ])
        
        story.append(
            _build_table(
                category_rows,
                [1.6 * inch, 1.1 * inch, 1.2 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch],
                colors.HexColor("#16a085"),
            )
        )
        story.append(Spacer(1, 0.2 * inch))
    
    # Collection point contributions - Use actual revenue/costs
    collection_points = report_data.get("collection_points", [])
    if collection_points:
        story.append(Paragraph("Collection Point Contributions", heading_style))
        cp_rows = [
            ["Collection Point", "Transactions", "Total Quantity", "Revenue", "Cost", "Net Value"]
        ]
        total_cp_revenue = 0
        total_cp_cost = 0
        total_cp_net = 0
        
        for cp in collection_points:
            cp_revenue = cp.get("total_revenue", 0)
            cp_cost = cp.get("total_cost", 0)
            cp_net = cp.get("net_value", 0)
            
            total_cp_revenue += cp_revenue
            total_cp_cost += cp_cost
            total_cp_net += cp_net
            
            cp_rows.append(
                [
                    cp.get("collection_point", "Unassigned"),
                    str(cp.get("transaction_count", 0)),
                    _format_quantity(cp.get("total_quantity_kg", 0)),
                    _format_currency(cp_revenue),
                    _format_currency(cp_cost),
                    _format_currency(cp_net),
                ]
            )
        
        # Add totals row
        cp_rows.append([
            "<b>Total</b>",
            "",
            "",
            f"<b>{_format_currency(total_cp_revenue)}</b>",
            f"<b>{_format_currency(total_cp_cost)}</b>",
            f"<b>{_format_currency(total_cp_net)}</b>",
        ])
        
        story.append(
            _build_table(
                cp_rows,
                [1.6 * inch, 1.0 * inch, 1.2 * inch, 1.3 * inch, 1.3 * inch, 1.3 * inch],
                colors.HexColor("#2c3e50"),
            )
        )
        story.append(
            Paragraph(
                "Use this view to benchmark efficiencies across yards, plants, and MRF locations. Low-yield points may require process interventions or capacity planning.",
                note_style,
            )
        )
        story.append(Spacer(1, 0.2 * inch))
    
    # Daily trend data - Use actual revenue/costs from entries
    daily_trends = report_data.get("charts", {}).get("daily_trends", [])
    if daily_trends:
        story.append(Paragraph("Daily Net Waste Value Trend", heading_style))
        trend_rows = [["Date", "Transactions", "Revenue", "Cost", "Net Value"]]
        total_trend_revenue = 0
        total_trend_cost = 0
        total_trend_nwv = 0
        
        for day in daily_trends:
            day_revenue = day.get("revenue", 0) or day.get("actual_revenue", 0)
            day_cost = day.get("cost", 0) or day.get("actual_cost", 0)
            day_nwv = day.get("net_value", 0)
            
            total_trend_revenue += day_revenue
            total_trend_cost += day_cost
            total_trend_nwv += day_nwv
            
            trend_rows.append(
                [
                    day.get("date", ""),
                    str(day.get("transactions", 0)),
                    _format_currency(day_revenue),
                    _format_currency(day_cost),
                    _format_currency(day_nwv),
                ]
            )
        
        # Add totals row
        trend_rows.append([
            "<b>Total</b>",
            "",
            f"<b>{_format_currency(total_trend_revenue)}</b>",
            f"<b>{_format_currency(total_trend_cost)}</b>",
            f"<b>{_format_currency(total_trend_nwv)}</b>",
        ])
        
        story.append(
            _build_table(
                trend_rows,
                [1.2 * inch, 1.0 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch],
                colors.HexColor("#d35400"),
            )
        )
        story.append(
            Paragraph(
                "Trend analysis highlights revenue/cost spikes that typically map to production shifts, supplier pick-ups, or disposal events. Use this to identify operational anomalies.",
                note_style,
            )
        )
        story.append(Spacer(1, 0.2 * inch))
    
    # Transaction details (summarized) - Use actual revenue/costs
    transactions = report_data.get("transactions", [])
    if transactions:
        story.append(Paragraph("Transaction Register (Detailed View)", heading_style))
        transaction_rows = [
            ["Date & Time", "Material / Category", "Collection Point", "Quantity", "Revenue", "Cost", "Net"]
        ]
        total_txn_revenue = 0
        total_txn_cost = 0
        total_txn_net = 0
        
        for txn in transactions:
            # Use actual revenue/cost if available (from entries), otherwise use expected
            txn_revenue = txn.get("revenue", 0)  # Already uses actual from entries
            txn_cost = txn.get("cost", 0)  # Already uses actual from entries
            txn_net = txn.get("net_value", 0)
            
            total_txn_revenue += txn_revenue
            total_txn_cost += txn_cost
            total_txn_net += txn_net
            
            # Add indicator if actual vs expected
            revenue_indicator = ""
            cost_indicator = ""
            if txn.get("has_revenue_entry"):
                revenue_indicator = " ✓"
            if txn.get("has_cost_entry"):
                cost_indicator = " ✓"
            
            transaction_rows.append(
                [
                    txn.get("date", ""),
                    f"{txn.get('material_type', '')} ({txn.get('category', '')})",
                    txn.get("collection_point", "—") or "—",
                    _format_quantity(txn.get("quantity_kg", 0)),
                    _format_currency(txn_revenue) + revenue_indicator,
                    _format_currency(txn_cost) + cost_indicator,
                    _format_currency(txn_net),
                ]
            )
        
        # Add totals row
        transaction_rows.append([
            "<b>Total</b>",
            "",
            "",
            "",
            f"<b>{_format_currency(total_txn_revenue)}</b>",
            f"<b>{_format_currency(total_txn_cost)}</b>",
            f"<b>{_format_currency(total_txn_net)}</b>",
        ])
        
        story.append(
            KeepTogether(
                [
                    _build_table(
                        transaction_rows,
                        [1.2 * inch, 1.6 * inch, 1.4 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch, 1.1 * inch],
                        colors.HexColor("#7f8c8d"),
                    ),
                    Paragraph(
                        "Every row represents a financial ledger entry created via the Waste Entry portal. Net values are computed post quality adjustments and disposal burden allocations. ✓ indicates actual revenue/cost entries.",
                        note_style,
                    ),
                ]
            )
        )
        story.append(Spacer(1, 0.2 * inch))
    
    # Advanced Analytical Insights
    variance_analysis = report_data.get("variance_analysis", {})
    profitability_metrics = report_data.get("profitability_metrics", {})
    performance_metrics = report_data.get("performance_metrics", {})
    benchmark_comparison = report_data.get("benchmark_comparison", {})
    
    if variance_analysis or profitability_metrics or performance_metrics:
        story.append(PageBreak())
        story.append(Paragraph("Advanced Analytical Insights", heading_style))
        
        # Variance Analysis
        if variance_analysis:
            story.append(Paragraph("Variance Analysis", sub_heading_style))
            variance_rows = [
                ["Metric", "Value"],
                ["Revenue Variance", _format_currency(variance_analysis.get("revenue_variance", 0)) + f" ({variance_analysis.get('revenue_variance_percent', 0):+.1f}%)"],
                ["Cost Variance", _format_currency(variance_analysis.get("cost_variance", 0)) + f" ({variance_analysis.get('cost_variance_percent', 0):+.1f}%)"],
                ["Net Variance Impact", _format_currency(variance_analysis.get("net_variance_impact", 0))],
            ]
            story.append(
                _build_table(
                    variance_rows,
                    [3.5 * inch, 2.8 * inch],
                    colors.HexColor("#e67e22"),
                )
            )
            story.append(Spacer(1, 0.15 * inch))
        
        # Profitability Metrics
        if profitability_metrics:
            story.append(Paragraph("Profitability Metrics", sub_heading_style))
            profit_rows = [
                ["Metric", "Value"],
                ["Profit Margin", _format_percentage(profitability_metrics.get("profit_margin_percent", 0))],
                ["Cost Efficiency Ratio", f"{profitability_metrics.get('cost_efficiency_ratio', 0):.2f}x"],
                ["ROI (Return on Investment)", _format_percentage(profitability_metrics.get("roi_percentage", 0))],
                ["Revenue Efficiency", _format_currency(profitability_metrics.get("revenue_efficiency_per_kg", 0)) + "/kg"],
            ]
            story.append(
                _build_table(
                    profit_rows,
                    [3.5 * inch, 2.8 * inch],
                    colors.HexColor("#27ae60"),
                )
            )
            story.append(Spacer(1, 0.15 * inch))
        
        # Performance Metrics
        if performance_metrics:
            story.append(Paragraph("Performance Metrics", sub_heading_style))
            perf_rows = [
                ["Metric", "Value"],
                ["Avg Transaction Value", _format_currency(performance_metrics.get("avg_transaction_value", 0))],
                ["Avg Transaction Cost", _format_currency(performance_metrics.get("avg_transaction_cost", 0))],
                ["Avg Transaction NWV", _format_currency(performance_metrics.get("avg_transaction_nwv", 0))],
                ["Recyclable Efficiency", _format_percentage(performance_metrics.get("recyclable_efficiency_percent", 0))],
                ["Performance Trend", performance_metrics.get("performance_trend", "stable").title()],
                ["Quality Revenue Ratio", _format_percentage(performance_metrics.get("quality_revenue_ratio_percent", 0))],
            ]
            story.append(
                _build_table(
                    perf_rows,
                    [3.5 * inch, 2.8 * inch],
                    colors.HexColor("#3498db"),
                )
            )
            story.append(Spacer(1, 0.15 * inch))
        
        # Benchmark Comparison
        if benchmark_comparison:
            story.append(Paragraph("Benchmark Comparison", sub_heading_style))
            benchmark_source = "Calculated from historical data" if benchmark_comparison.get("is_calculated") else "Industry standard estimates"
            bench_rows = [
                ["Metric", "Value"],
                ["Performance Rating", benchmark_comparison.get("performance_rating", "N/A").title()],
                ["Revenue/kg vs Industry", _format_currency(benchmark_comparison.get("revenue_per_kg_vs_industry", 0))],
                ["Cost/kg vs Industry", _format_currency(benchmark_comparison.get("cost_per_kg_vs_industry", 0))],
                ["Profit Margin vs Industry", _format_percentage(benchmark_comparison.get("profit_margin_vs_industry", 0))],
                ["Diversion Rate vs Industry", _format_percentage(benchmark_comparison.get("diversion_rate_vs_industry", 0))],
            ]
            story.append(
                _build_table(
                    bench_rows,
                    [3.5 * inch, 2.8 * inch],
                    colors.HexColor("#9b59b6"),
                )
            )
            story.append(Paragraph(f"<i>Benchmark source: {benchmark_source}</i>", note_style))
            story.append(Spacer(1, 0.15 * inch))
        
        # Data Quality Indicators
        data_quality = report_data.get("data_quality", {})
        if data_quality:
            story.append(Paragraph("Data Quality & Completeness", sub_heading_style))
            dq_rows = [
                ["Indicator", "Value"],
                ["Data Completeness", _format_percentage(data_quality.get("data_completeness_percent", 0))],
                ["Revenue Entries", f"{data_quality.get('revenue_entries_count', 0)} entries"],
                ["Cost Entries", f"{data_quality.get('cost_entries_count', 0)} entries"],
                ["Transactions with Revenue", f"{data_quality.get('transactions_with_revenue', 0)}"],
                ["Transactions with Costs", f"{data_quality.get('transactions_with_costs', 0)}"],
            ]
            story.append(
                _build_table(
                    dq_rows,
                    [3.5 * inch, 2.8 * inch],
                    colors.HexColor("#95a5a6"),
                )
            )
            story.append(Spacer(1, 0.2 * inch))
    
    # Recommendations
    recommendations = report_data.get("recommendations", [])
    if recommendations:
        story.append(Paragraph("Operational Recommendations & Next Steps", heading_style))
        for idx, rec in enumerate(recommendations, 1):
            story.append(Paragraph(f"{idx}. {rec}", normal_small))
        story.append(Spacer(1, 0.2 * inch))
    
    story.append(
        Paragraph(
            "These recommendations are data-driven, combining segregation performance, price benchmarks, and disposal liabilities to guide operational decisions.",
            note_style,
        )
    )
    
    # Risk alerts
    risk_alerts = report_data.get("risk_alerts", [])
    if risk_alerts:
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Risk Alerts & Compliance Flags", heading_style))
        for alert in risk_alerts:
            story.append(Paragraph(f"• {alert}", normal_small))
        story.append(
            Paragraph(
                "Address the above items with your operations and compliance teams to prevent regulatory exposure and avoidable cost overruns.",
                note_style,
            )
        )
    
    # Footer
    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph(
        "Prepared by the Automated Waste Financial Ledger © "
        f"{datetime.now().year}. Data sources include on-ground collection records, segregation audits, and indexed commodity pricing.",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story)
    
    return filename

