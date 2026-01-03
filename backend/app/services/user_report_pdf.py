"""User Report PDF generation - creates branded PDF reports."""
import logging
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    KeepTogether, Image, Flowable
)
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
import math
import colorsys

from app.services.user_report_data import UserReportData
from app.services.user_report_narrative import UserReportNarrative

logger = logging.getLogger(__name__)

# Ragard brand colors (dark theme)
RAGARD_DARK = HexColor("#0F172A")  # slate-900
RAGARD_SURFACE = HexColor("#1E293B")  # slate-800
RAGARD_ACCENT = HexColor("#22D3EE")  # cyan-400
RAGARD_TEXT_PRIMARY = HexColor("#F1F5F9")  # slate-100
RAGARD_TEXT_SECONDARY = HexColor("#94A3B8")  # slate-400
RAGARD_SUCCESS = HexColor("#10B981")  # green-500
RAGARD_DANGER = HexColor("#EF4444")  # red-500


def _get_regard_label(score: Optional[float]) -> str:
    """Get label for regard score range."""
    if score is None:
        return "No Score Yet"
    if score >= 80:
        return "Full Regard: highly regarded YOLO machine"
    elif score >= 60:
        return "High Regard: pretty regarded with strong degen tendencies"
    elif score >= 40:
        return "Mid Regard: moderately regarded, half investor half gambler"
    elif score >= 20:
        return "Low Regard: slightly regarded, recovering degen"
    else:
        return "0 Regard: not regarded, actually doing the boring smart stuff"


def _format_currency(value: Optional[float]) -> str:
    """Format value as currency."""
    if value is None:
        return "N/A"
    if value >= 0:
        return f"${value:,.2f}"
    else:
        return f"-${abs(value):,.2f}"


def _format_percentage(value: Optional[float]) -> str:
    """Format value as percentage."""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def _format_date(date_str: Optional[str]) -> str:
    """Format ISO date string for display."""
    if not date_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y")
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else date_str


def _format_holding_period(seconds: Optional[float]) -> str:
    """Format holding period in seconds to human-readable string."""
    if seconds is None:
        return "N/A"
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h"
    else:
        return f"{int(seconds / 86400)}d"


class ChartFlowable(Flowable):
    """Custom flowable to draw charts."""
    def __init__(self, chart_type: str, data: List[Dict[str, Any]], width=6*inch, height=2*inch, **kwargs):
        Flowable.__init__(self)
        self.chart_type = chart_type
        self.data = data
        self.width = width
        self.height = height
        self.kwargs = kwargs
        
    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)
    
    def draw(self):
        """Draw the chart."""
        canvas_obj = self.canv
        canvas_obj.saveState()
        
        if self.chart_type == "cumulative_pnl":
            self._draw_cumulative_pnl(canvas_obj)
        elif self.chart_type == "pnl_distribution":
            self._draw_pnl_distribution(canvas_obj)
        elif self.chart_type == "win_rate_time":
            self._draw_win_rate_time(canvas_obj)
        
        canvas_obj.restoreState()
    
    def _draw_cumulative_pnl(self, canvas_obj):
        """Draw cumulative PnL line chart."""
        if not self.data:
            return
        
        margin = 0.4 * inch
        chart_width = self.width - 2 * margin
        chart_height = self.height - 2 * margin
        
        # Find min/max for scaling
        pnls = [d["cumulativePnl"] for d in self.data]
        min_pnl = min(pnls)
        max_pnl = max(pnls)
        pnl_range = max_pnl - min_pnl if max_pnl != min_pnl else 1
        
        # Draw axes
        x0 = margin
        y0 = margin + 0.2 * inch  # Extra space for x-axis labels
        x1 = self.width - margin
        y1 = self.height - margin
        
        canvas_obj.setStrokeColor(RAGARD_ACCENT)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(x0, y0, x1, y0)  # X-axis
        canvas_obj.line(x0, y0, x0, y1)  # Y-axis
        
        # Draw zero line if applicable
        if min_pnl < 0 < max_pnl:
            zero_y = y0 + (abs(min_pnl) / pnl_range) * (y1 - y0)
            canvas_obj.setStrokeColor(RAGARD_TEXT_SECONDARY)
            canvas_obj.setLineWidth(0.5)
            canvas_obj.setDash([2, 2])
            canvas_obj.line(x0, zero_y, x1, zero_y)
            canvas_obj.setDash([])
        
        # Draw line
        canvas_obj.setStrokeColor(RAGARD_ACCENT)
        canvas_obj.setLineWidth(2)
        
        if len(self.data) > 1:
            path = canvas_obj.beginPath()
            first = True
            for i, point in enumerate(self.data):
                x = x0 + (i / (len(self.data) - 1)) * chart_width
                y = y0 + ((point["cumulativePnl"] - min_pnl) / pnl_range) * (y1 - y0)
                if first:
                    path.moveTo(x, y)
                    first = False
                else:
                    path.lineTo(x, y)
            canvas_obj.drawPath(path, stroke=1, fill=0)
        
        # Y-axis labels
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
        canvas_obj.drawString(x0 - 0.4 * inch, y0 - 0.05 * inch, f"${min_pnl:,.0f}")
        canvas_obj.drawString(x0 - 0.4 * inch, y1 - 0.05 * inch, f"${max_pnl:,.0f}")
        if min_pnl < 0 < max_pnl:
            zero_y = y0 + (abs(min_pnl) / pnl_range) * (y1 - y0)
            canvas_obj.drawString(x0 - 0.25 * inch, zero_y - 0.05 * inch, "$0")
        
        # X-axis labels (dates) - show first, middle, last
        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
        if len(self.data) > 0:
            # First date
            first_date = self.data[0].get("date", "")
            if first_date:
                try:
                    dt = datetime.fromisoformat(first_date.replace("Z", "+00:00"))
                    date_str = dt.strftime("%m/%d")
                    canvas_obj.drawCentredString(x0, y0 - 0.15 * inch, date_str)
                except Exception:
                    pass
            
            # Last date
            last_date = self.data[-1].get("date", "")
            if last_date:
                try:
                    dt = datetime.fromisoformat(last_date.replace("Z", "+00:00"))
                    date_str = dt.strftime("%m/%d")
                    canvas_obj.drawCentredString(x1, y0 - 0.15 * inch, date_str)
                except Exception:
                    pass
            
            # Middle date (if enough data points)
            if len(self.data) > 2:
                mid_idx = len(self.data) // 2
                mid_date = self.data[mid_idx].get("date", "")
                if mid_date:
                    try:
                        dt = datetime.fromisoformat(mid_date.replace("Z", "+00:00"))
                        date_str = dt.strftime("%m/%d")
                        mid_x = x0 + (mid_idx / (len(self.data) - 1)) * chart_width
                        canvas_obj.drawCentredString(mid_x, y0 - 0.15 * inch, date_str)
                    except Exception:
                        pass
        
        # Axis labels
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
        canvas_obj.drawString(x0 + chart_width / 2 - 0.3 * inch, y0 - 0.3 * inch, "Date")
        # Y-axis label - centered vertically
        canvas_obj.saveState()
        canvas_obj.translate(0.15 * inch, y0 + chart_height / 2)
        canvas_obj.rotate(90)
        text_width = canvas_obj.stringWidth("Cumulative Realized PnL ($)", "Helvetica-Bold", 8)
        canvas_obj.drawString(-text_width / 2, 0, "Cumulative Realized PnL ($)")
        canvas_obj.restoreState()
        
        # Add value indicator on the most recent data point
        if len(self.data) > 0:
            last_point = self.data[-1]
            if len(self.data) > 1:
                last_x = x0 + ((len(self.data) - 1) / (len(self.data) - 1)) * chart_width
            else:
                last_x = x0
            last_y = y0 + ((last_point["cumulativePnl"] - min_pnl) / pnl_range) * (y1 - y0)
            
            # Draw circle indicator (slightly smaller)
            canvas_obj.setFillColor(RAGARD_ACCENT)
            canvas_obj.setStrokeColor(colors.white)
            indicator_radius = 0.07 * inch
            canvas_obj.setLineWidth(2)
            canvas_obj.circle(last_x, last_y, indicator_radius, fill=1, stroke=1)
            
            # Draw value label with background box for better readability
            canvas_obj.setFont("Helvetica-Bold", 10)
            value_text = f"${last_point['cumulativePnl']:,.0f}"
            text_width = canvas_obj.stringWidth(value_text, "Helvetica-Bold", 10)
            text_height = 0.12 * inch
            
            # Position label above the point
            label_y = last_y + 0.25 * inch
            # Make sure label doesn't go off chart - if it would, put it below
            if label_y + text_height > y1:
                label_y = last_y - 0.35 * inch
            
            # Draw background box for the label
            padding = 0.05 * inch
            box_x = last_x - text_width / 2 - padding
            box_y = label_y - text_height / 2
            box_width = text_width + 2 * padding
            box_height = text_height + 2 * padding
            
            canvas_obj.setFillColor(RAGARD_DARK)
            canvas_obj.setStrokeColor(RAGARD_ACCENT)
            canvas_obj.setLineWidth(1.5)
            canvas_obj.roundRect(box_x, box_y, box_width, box_height, 0.03 * inch, fill=1, stroke=1)
            
            # Draw the text on top
            canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
            canvas_obj.drawCentredString(last_x, label_y, value_text)
    
    def _draw_pnl_distribution(self, canvas_obj):
        """Draw PnL distribution bar chart."""
        if not self.data:
            return
        
        margin = 0.4 * inch
        chart_width = self.width - 2 * margin
        chart_height = self.height - 2 * margin
        
        max_count = max(d["count"] for d in self.data)
        bar_width = chart_width / len(self.data) * 0.75
        bar_spacing = chart_width / len(self.data) * 0.25
        
        x0 = margin
        y0 = margin + 0.2 * inch  # Extra space for labels
        
        # Draw Y-axis
        canvas_obj.setStrokeColor(RAGARD_ACCENT)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(x0, y0, x0, y0 + chart_height)  # Y-axis
        canvas_obj.line(x0, y0 + chart_height, x0 + chart_width, y0 + chart_height)  # X-axis
        
        # Y-axis labels
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
        canvas_obj.drawString(x0 - 0.3 * inch, y0 + chart_height - 0.05 * inch, "0")
        if max_count > 0:
            canvas_obj.drawString(x0 - 0.4 * inch, y0 - 0.05 * inch, str(max_count))
        
        for i, item in enumerate(self.data):
            bar_height = (item["count"] / max_count) * chart_height if max_count > 0 else 0
            x = x0 + i * (bar_width + bar_spacing) + bar_spacing / 2
            y = y0 + chart_height - bar_height
            
            # Color based on range (red for negative, green for positive)
            if item["range"].startswith("-") or item["range"] == "<-$1k":
                color = RAGARD_DANGER
            elif item["range"].startswith("$0") or item["range"] == ">$1k":
                color = RAGARD_SUCCESS
            else:
                color = RAGARD_ACCENT
            
            canvas_obj.setFillColor(color)
            canvas_obj.rect(x, y, bar_width, bar_height, fill=1, stroke=0)
            
            # Count label on top of bar
            canvas_obj.setFont("Helvetica", 7)
            canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
            if bar_height > 0.15 * inch:  # Only show if bar is tall enough
                canvas_obj.drawCentredString(x + bar_width / 2, y - 0.15 * inch, str(item["count"]))
            
            # Range label below x-axis
            canvas_obj.setFont("Helvetica", 6)
            canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
            # Rotate text for better fit
            canvas_obj.saveState()
            canvas_obj.translate(x + bar_width / 2, y0 + chart_height + 0.2 * inch)
            canvas_obj.rotate(-45)
            canvas_obj.drawCentredString(0, 0, item["range"])
            canvas_obj.restoreState()
        
        # Axis labels
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
        canvas_obj.drawString(x0 + chart_width / 2 - 0.4 * inch, y0 + chart_height + 0.35 * inch, "PnL Range")
        canvas_obj.saveState()
        canvas_obj.translate(0.15 * inch, y0 + chart_height / 2)
        canvas_obj.rotate(90)
        canvas_obj.drawString(0, 0, "Number of Trades")
        canvas_obj.restoreState()
    
    def _draw_win_rate_time(self, canvas_obj):
        """Draw win rate by time of day bar chart."""
        if not self.data:
            return
        
        margin = 0.4 * inch
        chart_width = self.width - 2 * margin
        chart_height = self.height - 2 * margin
        
        max_win_rate = max(d["winRate"] for d in self.data) if self.data else 1.0
        bar_width = chart_width / len(self.data) * 0.75
        bar_spacing = chart_width / len(self.data) * 0.25
        
        x0 = margin
        y0 = margin + 0.2 * inch
        
        # Draw Y-axis
        canvas_obj.setStrokeColor(RAGARD_ACCENT)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(x0, y0, x0, y0 + chart_height)  # Y-axis
        canvas_obj.line(x0, y0 + chart_height, x0 + chart_width, y0 + chart_height)  # X-axis
        
        # Y-axis labels (0% to 100%)
        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
        canvas_obj.drawString(x0 - 0.25 * inch, y0 + chart_height - 0.05 * inch, "0%")
        canvas_obj.drawString(x0 - 0.3 * inch, y0 - 0.05 * inch, "100%")
        canvas_obj.drawString(x0 - 0.3 * inch, y0 + chart_height / 2 - 0.05 * inch, "50%")
        
        for i, item in enumerate(self.data):
            win_rate = item["winRate"]
            bar_height = (win_rate / 1.0) * chart_height  # Win rate is 0-1
            x = x0 + i * (bar_width + bar_spacing) + bar_spacing / 2
            y = y0 + chart_height - bar_height
            
            # Color based on win rate (green for high, red for low)
            if win_rate >= 0.6:
                color = RAGARD_SUCCESS
            elif win_rate >= 0.4:
                color = RAGARD_ACCENT
            else:
                color = RAGARD_DANGER
            
            canvas_obj.setFillColor(color)
            canvas_obj.rect(x, y, bar_width, bar_height, fill=1, stroke=0)
            
            # Win rate label on top of bar
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
            if bar_height > 0.15 * inch:
                canvas_obj.drawCentredString(x + bar_width / 2, y - 0.15 * inch, f"{win_rate * 100:.0f}%")
            
            # Trade count label below
            canvas_obj.setFont("Helvetica", 7)
            canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
            canvas_obj.drawCentredString(x + bar_width / 2, y0 + chart_height + 0.08 * inch, f"n={item['trades']}")
            
            # Time period label
            canvas_obj.setFont("Helvetica", 7)
            canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
            canvas_obj.saveState()
            canvas_obj.translate(x + bar_width / 2, y0 + chart_height + 0.25 * inch)
            canvas_obj.rotate(-45)
            canvas_obj.drawCentredString(0, 0, item["label"])
            canvas_obj.restoreState()
        
        # Axis labels
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
        canvas_obj.drawString(x0 + chart_width / 2 - 0.5 * inch, y0 + chart_height + 0.4 * inch, "Trading Time Period")
        canvas_obj.saveState()
        canvas_obj.translate(0.15 * inch, y0 + chart_height / 2)
        canvas_obj.rotate(90)
        canvas_obj.drawString(0, 0, "Win Rate (%)")
        canvas_obj.restoreState()


def _get_regard_color(score: Optional[float]) -> HexColor:
    """Get color for regard score using HSL gradient (green->yellow->red)."""
    if score is None:
        return RAGARD_TEXT_SECONDARY
    
    clamped_score = max(0, min(100, score))
    
    # Convert HSL to RGB approximation
    if clamped_score <= 50:
        # Green (120deg) to Yellow (60deg)
        t = clamped_score / 50
        hue = 120 - (t * 60)
        saturation = 0.7 + (t * 0.1)
        lightness = 0.5 - (t * 0.05)
    else:
        # Yellow (60deg) to Red (0deg)
        t = (clamped_score - 50) / 50
        hue = 60 - (t * 60)
        saturation = 0.8 + (t * 0.15)
        lightness = 0.45 - (t * 0.05)
    
    # Convert HSL to RGB (simplified)
    import colorsys
    rgb = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
    return HexColor(f"#{int(rgb[0]*255):02x}{int(rgb[1]*255):02x}{int(rgb[2]*255):02x}")


class GaugeFlowable(Flowable):
    """Custom flowable to draw the Regard Score gauge."""
    def __init__(self, score, color, size=2.8*inch):
        Flowable.__init__(self)
        self.score = score
        self.color = color
        self.size = size
        self.radius = size / 2 - 0.2 * inch
        self.stroke_width = 0.25 * inch
        
    def wrap(self, availWidth, availHeight):
        return (self.size, self.size)
    
    def draw(self):
        """Draw the gauge circle with number."""
        canvas_obj = self.canv
        canvas_obj.saveState()
        
        center_x = self.size / 2
        center_y = self.size / 2
        
        # Draw background circle (gray, full circle)
        canvas_obj.setStrokeColor(RAGARD_SURFACE)
        canvas_obj.setFillColor(RAGARD_SURFACE)
        canvas_obj.setLineWidth(self.stroke_width)
        canvas_obj.circle(center_x, center_y, self.radius, fill=0, stroke=1)
        
        # Draw score arc (colored, partial circle)
        if self.score is not None and self.score > 0:
            score_pct = self.score / 100.0
            # Draw arc from 90 degrees (top) clockwise
            start_angle = 90  # Top of circle
            extent = 360 * score_pct
            
            canvas_obj.setStrokeColor(self.color)
            canvas_obj.setLineWidth(self.stroke_width)
            canvas_obj.setLineCap(1)  # Round cap
            canvas_obj.setLineJoin(1)  # Round join
            
            # Draw arc using many small line segments for smooth curve
            num_segments = max(60, int(extent))  # At least 60 segments, more for larger arcs
            segment_extent = extent / num_segments
            
            path = canvas_obj.beginPath()
            first_point = True
            
            for i in range(num_segments + 1):
                # Subtract to go clockwise (in standard math coords, positive goes counter-clockwise)
                angle = start_angle - (i * segment_extent)
                rad = math.radians(angle)
                x = center_x + self.radius * math.cos(rad)
                y = center_y + self.radius * math.sin(rad)
                
                if first_point:
                    path.moveTo(x, y)
                    first_point = False
                else:
                    path.lineTo(x, y)
            
            canvas_obj.drawPath(path, stroke=1, fill=0)
        
        # Draw number in center (colored text)
        score_text = str(int(self.score)) if self.score is not None else "N/A"
        canvas_obj.setFillColor(self.color)
        canvas_obj.setFont("Helvetica-Bold", 80)
        # Center the text vertically
        text_y = center_y - 0.25 * inch
        canvas_obj.drawCentredString(center_x, text_y, score_text)
        
        # Draw "/100" below score in smaller text
        canvas_obj.setFont("Helvetica", 16)
        canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
        canvas_obj.drawCentredString(center_x, text_y - 0.35 * inch, "/100")
        
        canvas_obj.restoreState()


def _create_header_footer(canvas_obj, doc):
    """Add header and footer to each page with dark background."""
    canvas_obj.saveState()
    
    # Draw dark background for entire page
    canvas_obj.setFillColor(RAGARD_DARK)
    canvas_obj.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
    
    # Footer
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.setFillColor(RAGARD_TEXT_SECONDARY)
    canvas_obj.drawString(
        inch,
        0.5 * inch,
        f"Ragard · Generated on {datetime.now().strftime('%B %d, %Y')} · This is not financial advice."
    )
    
    # Header line
    canvas_obj.setStrokeColor(RAGARD_ACCENT)
    canvas_obj.setLineWidth(2)
    canvas_obj.line(inch, letter[1] - 0.5 * inch, letter[0] - inch, letter[1] - 0.5 * inch)
    
    canvas_obj.restoreState()


def _generate_user_report_pdf_sync(data: UserReportData, narrative: UserReportNarrative) -> bytes:
    """
    Generate a branded PDF report for the user (synchronous version).
    
    Args:
        data: UserReportData with all metrics
        narrative: UserReportNarrative with AI-generated text
        
    Returns:
        PDF as bytes
    """
    buffer = BytesIO()
    
    # Set PDF metadata
    title = f"Ragard Trading Report - {data.display_name}"
    author = "Ragard"
    subject = "Trading Performance Analysis"
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=title,
        author=author,
        subject=subject,
    )
    
    # Build story (content)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=RAGARD_ACCENT,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    
    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=RAGARD_ACCENT,
        spaceAfter=12,
        spaceBefore=12,
        fontName="Helvetica-Bold",
    )
    
    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["Normal"],
        fontSize=10,
        textColor=RAGARD_TEXT_PRIMARY,
        spaceAfter=6,
        leading=14,
    )
    
    # ===== COVER PAGE =====
    story.append(Spacer(1, 1.5 * inch))
    
    # Logo (simple text-based logo) - "Ragard" with only R capitalized, RA in white
    # We'll use a custom flowable to draw mixed colors
    class LogoFlowable(Flowable):
        def __init__(self):
            Flowable.__init__(self)
        def wrap(self, availWidth, availHeight):
            self.width = availWidth
            return (availWidth, 0.7 * inch)
        def draw(self):
            canvas_obj = self.canv
            canvas_obj.saveState()
            center_x = self.width / 2
            y_pos = 0.5 * inch
            
            # Draw "Ra" in white (Ra capitalized) - using Helvetica as closest to Space Grotesk
            # Space Grotesk is a geometric sans-serif, Helvetica is similar enough for PDF
            canvas_obj.setFont("Helvetica-Bold", 52)
            canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
            text_width_ra = canvas_obj.stringWidth("Ra", "Helvetica-Bold", 52)
            
            # Draw "gard" in cyan
            canvas_obj.setFillColor(RAGARD_ACCENT)
            text_width_gard = canvas_obj.stringWidth("gard", "Helvetica-Bold", 52)
            
            # Center the entire "Ragard" text
            total_width = text_width_ra + text_width_gard
            start_x = center_x - total_width / 2
            
            # Draw "Ra" in white
            canvas_obj.setFillColor(RAGARD_TEXT_PRIMARY)
            canvas_obj.drawString(start_x, y_pos, "Ra")
            
            # Draw "gard" in cyan
            canvas_obj.setFillColor(RAGARD_ACCENT)
            canvas_obj.drawString(start_x + text_width_ra, y_pos, "gard")
            
            canvas_obj.restoreState()
    
    logo = LogoFlowable()
    story.append(logo)
    story.append(Spacer(1, 0.2 * inch))
    
    # Divider line
    class DividerFlowable(Flowable):
        def __init__(self):
            Flowable.__init__(self)
        def wrap(self, availWidth, availHeight):
            self.width = availWidth
            return (availWidth, 0.15 * inch)
        def draw(self):
            canvas_obj = self.canv
            canvas_obj.saveState()
            center_x = self.width / 2
            line_width = 1.5 * inch
            canvas_obj.setStrokeColor(RAGARD_ACCENT)
            canvas_obj.setLineWidth(1)
            canvas_obj.line(center_x - line_width / 2, 0.05 * inch, center_x + line_width / 2, 0.05 * inch)
            canvas_obj.restoreState()
    
    divider = DividerFlowable()
    story.append(divider)
    story.append(Spacer(1, 0.2 * inch))
    
    # Title
    story.append(Paragraph("Trade Performance Report", title_style))
    story.append(Spacer(1, 0.4 * inch))
    
    # Subtitle
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=16,
        textColor=RAGARD_TEXT_SECONDARY,
        alignment=TA_CENTER,
        spaceAfter=0.3 * inch,
    )
    story.append(Paragraph(f"Personalized Analysis for", subtitle_style))
    
    name_style = ParagraphStyle(
        "Name",
        parent=styles["Normal"],
        fontSize=18,
        textColor=RAGARD_ACCENT,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        spaceAfter=0.4 * inch,
    )
    story.append(Paragraph(data.display_name, name_style))
    
    # Date
    date_style = ParagraphStyle(
        "Date",
        parent=styles["Normal"],
        fontSize=11,
        textColor=RAGARD_TEXT_SECONDARY,
        alignment=TA_CENTER,
        spaceAfter=0.5 * inch,
    )
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", date_style))
    
    # Tagline
    tagline_style = ParagraphStyle(
        "Tagline",
        parent=styles["Italic"],
        fontSize=11,
        textColor=RAGARD_TEXT_SECONDARY,
        alignment=TA_CENTER,
        spaceAfter=0.3 * inch,
    )
    story.append(Paragraph("Powered by AI, fueled by your questionable decisions.", tagline_style))
    
    # Additional professional touch
    story.append(Spacer(1, 0.5 * inch))
    report_type_style = ParagraphStyle(
        "ReportType",
        parent=styles["Normal"],
        fontSize=9,
        textColor=RAGARD_TEXT_SECONDARY,
        alignment=TA_CENTER,
    )
    story.append(Paragraph("Comprehensive Trading Analytics & Performance Insights", report_type_style))
    
    story.append(PageBreak())
    
    # ===== SECTION 1: EXECUTIVE SUMMARY =====
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Regard Score gauge (visual circle with number)
    score_color = _get_regard_color(data.regard_score)
    
    # Create and add the gauge flowable - center it on the page
    gauge = GaugeFlowable(data.regard_score, score_color, size=2.8*inch)
    story.append(Spacer(1, 0.2 * inch))
    # Center the gauge using a table with centered alignment
    gauge_table = Table([[gauge]], colWidths=[6.5 * inch])
    gauge_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(KeepTogether([gauge_table]))
    
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=12,
        textColor=RAGARD_TEXT_SECONDARY,
        alignment=TA_CENTER,
    )
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(_get_regard_label(data.regard_score), label_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Summary stats table - verify win rate is consistent
    wins = data.wins
    losses = data.losses
    calculated_total = wins + losses
    
    # Use sample_size if it matches, otherwise recalculate
    if data.sample_size == calculated_total:
        total_trades = data.sample_size
    else:
        logger.warning(f"Sample size mismatch: {data.sample_size} vs {calculated_total}. Using {calculated_total}")
        total_trades = calculated_total
    
    # Recalculate win rate to be sure
    win_rate = wins / total_trades if total_trades > 0 else None
    
    stats_data = [
        ["Wins", str(wins)],
        ["Losses", str(losses)],
        ["Win Rate", _format_percentage(win_rate)],
        ["Total Trades", str(total_trades)],
    ]
    
    # Track which rows have PnL for coloring
    pnl_rows = []
    
    if data.time_window_start and data.time_window_end:
        stats_data.append(["Time Span", f"{_format_date(data.time_window_start)} to {_format_date(data.time_window_end)}"])
    
    if data.total_pnl is not None:
        pnl_rows.append((len(stats_data), data.total_pnl))
        stats_data.append(["Total Realized PnL", _format_currency(data.total_pnl)])
    
    # Add unrealized PnL if available
    if data.open_positions_unrealized_pnl is not None and data.open_positions_count > 0:
        pnl_rows.append((len(stats_data), data.open_positions_unrealized_pnl))
        stats_data.append(["Unrealized PnL (est.)", _format_currency(data.open_positions_unrealized_pnl)])
        
        # Show combined total
        total_combined = (data.total_pnl or 0) + data.open_positions_unrealized_pnl
        pnl_rows.append((len(stats_data), total_combined))
        stats_data.append(["Total PnL (realized + est. unrealized)", _format_currency(total_combined)])
    
    # Convert table data to Paragraphs with color coding for P/L values
    stats_table_data = []
    for row_idx, row in enumerate(stats_data):
        row_cells = []
        for col_idx, cell in enumerate(row):
            if col_idx == 1 and any(r[0] == row_idx for r in pnl_rows):
                # This is a P/L value - apply color
                pnl_value = next(r[1] for r in pnl_rows if r[0] == row_idx)
                color_hex = "#10B981" if pnl_value > 0 else ("#EF4444" if pnl_value < 0 else "#F1F5F9")
                colored_style = ParagraphStyle("ColoredBody", parent=body_style, textColor=HexColor(color_hex))
                row_cells.append(Paragraph(str(cell), colored_style))
            else:
                row_cells.append(Paragraph(str(cell), body_style))
        stats_table_data.append(row_cells)
    
    stats_table = Table(stats_table_data, colWidths=[2.3 * inch, 2.1 * inch])
    
    # Professional styling with alternating rows
    table_style = [
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    
    # Alternating row banding and bold left column
    for i in range(len(stats_data)):
        if i % 2 == 0:
            table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
        else:
            table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
        table_style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
    
    stats_table.setStyle(TableStyle(table_style))
    story.append(stats_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Executive summary paragraphs
    for para in narrative.executive_summary_paragraphs:
        story.append(Paragraph(para, body_style))
        story.append(Spacer(1, 0.1 * inch))
    
    # Add detailed score explanation
    story.append(Spacer(1, 0.3 * inch))
    score_explanation_style = ParagraphStyle(
        "ScoreExplanation",
        parent=styles["Heading3"],
        fontSize=14,
        textColor=RAGARD_ACCENT,
        spaceBefore=0.2 * inch,
        spaceAfter=0.2 * inch,
    )
    story.append(Paragraph("How Your Regard Score Was Calculated", score_explanation_style))
    
    # Introduction paragraph
    intro_text = (
        f"Your Regard Score of <b>{int(data.regard_score) if data.regard_score else 'N/A'}</b> "
        "is calculated using a multi-factor model that analyzes your trading behavior, performance, "
        "and decision-making patterns. Remember: this is an <i>inverted</i> scale where "
        "<b>100 = full degen YOLO machine</b> and <b>0 = disciplined boring investor</b>. "
        "Higher scores indicate more aggressive, speculative behavior."
    )
    story.append(Paragraph(intro_text, body_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Component breakdown
    component_heading = ParagraphStyle(
        "ComponentHeading",
        parent=styles["Normal"],
        fontSize=11,
        textColor=RAGARD_ACCENT,
        fontName="Helvetica-Bold",
        spaceAfter=0.1 * inch,
    )
    
    # 1. Win Rate Analysis
    story.append(Paragraph("1. Win Rate & Consistency", component_heading))
    if data.win_rate is not None and data.sample_size > 0:
        wr_pct = data.win_rate * 100
        if wr_pct >= 65:
            wr_impact = "Your strong win rate (65%+) suggests disciplined decision-making, which <b>lowers</b> your score. You're picking winners more often than not."
        elif wr_pct >= 50:
            wr_impact = "Your decent win rate (50-65%) shows you're slightly better than a coin flip. This keeps your score in the mid-range."
        elif wr_pct >= 35:
            wr_impact = "Your mediocre win rate (35-50%) suggests inconsistent decision-making, which <b>raises</b> your score. You're losing more often than winning."
        else:
            wr_impact = "Your low win rate (<35%) indicates poor trade selection or timing, significantly <b>raising</b> your score. Most of your trades are losers."
        
        # Sample size impact
        if data.sample_size >= 50:
            size_impact = f"With {data.sample_size} trades, we have high confidence in this assessment."
        elif data.sample_size >= 20:
            size_impact = f"With {data.sample_size} trades, we have moderate confidence. More data would improve accuracy."
        else:
            size_impact = f"With only {data.sample_size} trades, confidence is limited. The score is pulled toward the mid-range (40-60) until you build more history."
        
        story.append(Paragraph(f"{wr_impact} {size_impact}", body_style))
    else:
        story.append(Paragraph("Insufficient data to analyze win rate.", body_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # 2. Risk Management
    story.append(Paragraph("2. Risk Management & Position Sizing", component_heading))
    if data.avg_win_pnl and data.avg_loss_pnl:
        rr_ratio = abs(data.avg_win_pnl / data.avg_loss_pnl) if data.avg_loss_pnl != 0 else 0
        if rr_ratio > 1.5:
            risk_impact = (
                f"Your winners are significantly larger than your losers (risk/reward ratio: {rr_ratio:.2f}). "
                "This shows good risk management - you let winners run and cut losers early. This <b>lowers</b> your score."
            )
        elif rr_ratio < 0.67:
            risk_impact = (
                f"Your losers are significantly larger than your winners (risk/reward ratio: {rr_ratio:.2f}). "
                "Classic degen behavior - you cut winners early and hold losers hoping they'll come back. This <b>raises</b> your score."
            )
        else:
            risk_impact = (
                f"Your win and loss sizes are relatively balanced (risk/reward ratio: {rr_ratio:.2f}). "
                "This is neutral - neither helping nor hurting your score significantly."
            )
        story.append(Paragraph(risk_impact, body_style))
        
        # Add position sizing if available
        if data.avg_position_size and data.largest_position_size:
            if data.largest_position_size > data.avg_position_size * 3:
                sizing_note = (
                    f"Your largest position ({_format_currency(data.largest_position_size)}) is significantly larger than your average "
                    f"({_format_currency(data.avg_position_size)}), suggesting occasional YOLO plays that <b>raise</b> your score."
                )
            else:
                sizing_note = (
                    f"Your position sizing is relatively consistent (avg: {_format_currency(data.avg_position_size)}, "
                    f"max: {_format_currency(data.largest_position_size)}), showing discipline."
                )
            story.append(Paragraph(sizing_note, body_style))
    else:
        story.append(Paragraph("Insufficient data to analyze risk management.", body_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # 3. Trading Style & Behavior
    story.append(Paragraph("3. Trading Style & Holding Patterns", component_heading))
    style_parts = []
    
    if data.winner_avg_holding_period or data.loser_avg_holding_period:
        avg_hold = None
        if data.winner_avg_holding_period and data.loser_avg_holding_period:
            avg_hold = (data.winner_avg_holding_period + data.loser_avg_holding_period) / 2
        elif data.winner_avg_holding_period:
            avg_hold = data.winner_avg_holding_period
        elif data.loser_avg_holding_period:
            avg_hold = data.loser_avg_holding_period
        
        if avg_hold:
            if avg_hold < 900:
                style_impact = "You're a <b>scalper</b> - ultra-short holds (under 15 minutes). This high-frequency approach can be profitable but also chaotic, slightly raising your score."
            elif avg_hold < 86400:
                style_impact = "You're a <b>day trader</b> - in and out within the same day. This active approach shows you're not afraid to make moves, moderately raising your score."
            elif avg_hold < 432000:
                style_impact = "You're a <b>swing trader</b> - holding for days. This balanced approach keeps your score in the mid-range - not full degen, not full boomer."
            else:
                style_impact = "You're a <b>position trader</b> - holding for weeks or months. This patient approach shows discipline, lowering your score."
            style_parts.append(style_impact)
    
    # Long vs short bias
    if data.long_count > 0 or data.short_count > 0:
        total_sided = data.long_count + data.short_count
        if total_sided > 0:
            long_pct = (data.long_count / total_sided) * 100
            if long_pct > 90:
                side_impact = f"You're almost exclusively long ({long_pct:.0f}% of trades). Going long is the default, so this is neutral."
            elif long_pct < 10:
                side_impact = f"You're heavily short-biased ({100-long_pct:.0f}% shorts). Shorting requires balls and shows aggressive behavior, raising your score."
            elif long_pct > 60:
                side_impact = f"You're mostly long ({long_pct:.0f}% long, {100-long_pct:.0f}% short). This is typical and neutral."
            else:
                side_impact = f"You're balanced between long and short ({long_pct:.0f}% long, {100-long_pct:.0f}% short). This shows flexibility."
            style_parts.append(side_impact)
    
    if style_parts:
        story.append(Paragraph(" ".join(style_parts), body_style))
    else:
        story.append(Paragraph("Insufficient data to analyze trading style.", body_style))
    story.append(Spacer(1, 0.15 * inch))
    
    # 4. Open Positions & Unrealized P/L Analysis
    story.append(Paragraph("4. Open Positions & Unrealized P/L", component_heading))
    if data.open_positions_count > 0:
        open_intro = (
            f"You currently have <b>{data.open_positions_count} open position{'s' if data.open_positions_count != 1 else ''}</b> "
            "with <b>unrealized</b> P/L (paper gains/losses that haven't been locked in yet). "
            "These positions factor into your Regard Score because they reveal your current risk exposure."
        )
        story.append(Paragraph(open_intro, body_style))
        story.append(Spacer(1, 0.1 * inch))
        
        # Unrealized P/L analysis
        if data.open_positions_unrealized_pnl is not None:
            if data.open_positions_unrealized_pnl < -500:
                pnl_impact = (
                    f"<b>Unrealized losses:</b> {_format_currency(abs(data.open_positions_unrealized_pnl))} (paper losses on open positions). "
                    "Bagholding significant losers is classic degen behavior and <b>raises</b> your score. "
                    "Diamond hands or denial?"
                )
            elif data.open_positions_unrealized_pnl < 0:
                pnl_impact = (
                    f"<b>Unrealized losses:</b> {_format_currency(abs(data.open_positions_unrealized_pnl))} (paper losses on open positions). "
                    "Minor unrealized losses are normal."
                )
            elif data.open_positions_unrealized_pnl > 500:
                pnl_impact = (
                    f"<b>Unrealized gains:</b> {_format_currency(data.open_positions_unrealized_pnl)} (paper profits on open positions). "
                    "Letting winners run shows discipline and <b>lowers</b> your score."
                )
            else:
                pnl_impact = (
                    f"<b>Unrealized gains:</b> {_format_currency(data.open_positions_unrealized_pnl)} (paper profits on open positions)."
                )
            story.append(Paragraph(pnl_impact, body_style))
        
        # Long-term holds
        if data.open_positions_list:
            try:
                from datetime import timezone
                now_aware = datetime.now(timezone.utc)
                long_term_holds = [p for p in data.open_positions_list 
                                 if p.get("entry_time") and 
                                 (now_aware - datetime.fromisoformat(p["entry_time"].replace("Z", "+00:00"))).days > 30]
            except Exception as e:
                logger.warning(f"Could not calculate long-term holds: {e}")
                long_term_holds = []
            
            if long_term_holds:
                hold_impact = (
                    f"You have {len(long_term_holds)} long-term open position{'s' if len(long_term_holds) != 1 else ''} (30+ days). "
                    "Long-term holds can be patient conviction or stubborn bagholding."
                )
                story.append(Paragraph(hold_impact, body_style))
    else:
        no_opens_text = (
            "You have <b>no open positions</b> - all P/L is <b>realized</b> (locked in). "
            "Either disciplined exits or not currently trading."
        )
        story.append(Paragraph(no_opens_text, body_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Final summary
    summary_heading = ParagraphStyle(
        "SummaryHeading",
        parent=styles["Normal"],
        fontSize=11,
        textColor=RAGARD_SUCCESS,
        fontName="Helvetica-Bold",
        spaceAfter=0.1 * inch,
    )
    story.append(Paragraph("The Bottom Line", summary_heading))
    
    if data.regard_score is not None:
        if data.regard_score >= 80:
            bottom_line = "You're <b>highly regarded</b> - a certified degen. Full YOLO energy, maximum risk tolerance, questionable decisions. Embrace it."
        elif data.regard_score >= 60:
            bottom_line = "You're <b>pretty regarded</b> with strong degen tendencies. You take risks, make aggressive plays, and probably check your portfolio way too often."
        elif data.regard_score >= 40:
            bottom_line = "You're <b>moderately regarded</b> - half investor, half gambler. Sometimes disciplined, sometimes full send. The eternal struggle."
        elif data.regard_score >= 20:
            bottom_line = "You're <b>slightly regarded</b>, a recovering degen. Mostly disciplined with occasional lapses. You're learning, slowly."
        else:
            bottom_line = "You're <b>not regarded at all</b> - actually doing the boring smart stuff. Disciplined, patient, risk-managed. Congrats, you're no fun at parties."
        story.append(Paragraph(bottom_line, body_style))
    else:
        story.append(Paragraph("Score unavailable - need more data.", body_style))
    
    story.append(PageBreak())
    
    # ===== SECTION 2: PERFORMANCE ANALYTICS =====
    story.append(Paragraph("Performance Analytics", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Best/Worst trades
    if data.best_trade_pnl is not None or data.worst_trade_pnl is not None:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        extremes_data = []
        extremes_pnl_values = []  # Track (row_idx, pnl_value) for coloring
        
        if data.best_trade_pnl is not None:
            extremes_pnl_values.append((len(extremes_data), data.best_trade_pnl))
            extremes_data.append(["Best Trade PnL", _format_currency(data.best_trade_pnl)])
        if data.worst_trade_pnl is not None:
            extremes_pnl_values.append((len(extremes_data), data.worst_trade_pnl))
            extremes_data.append(["Worst Trade PnL", _format_currency(data.worst_trade_pnl)])
        if data.avg_win_pnl is not None:
            extremes_pnl_values.append((len(extremes_data), data.avg_win_pnl))
            extremes_data.append(["Average Win", _format_currency(data.avg_win_pnl)])
        if data.avg_loss_pnl is not None:
            extremes_pnl_values.append((len(extremes_data), data.avg_loss_pnl))
            extremes_data.append(["Average Loss", _format_currency(data.avg_loss_pnl)])
        
        # Convert table data to Paragraphs with color coding for P/L values
        extremes_table_data = []
        for row_idx, row in enumerate(extremes_data):
            row_cells = []
            for col_idx, cell in enumerate(row):
                if col_idx == 1 and any(r[0] == row_idx for r in extremes_pnl_values):
                    # This is a P/L value - apply color
                    pnl_value = next(r[1] for r in extremes_pnl_values if r[0] == row_idx)
                    color_hex = "#10B981" if pnl_value > 0 else ("#EF4444" if pnl_value < 0 else "#F1F5F9")
                    colored_style = ParagraphStyle("ColoredBody", parent=body_style, textColor=HexColor(color_hex))
                    row_cells.append(Paragraph(str(cell), colored_style))
                else:
                    row_cells.append(Paragraph(str(cell), body_style))
            extremes_table_data.append(row_cells)
        
        extremes_table = Table(extremes_table_data, colWidths=[2.3 * inch, 2.1 * inch])
        
        # Professional styling with alternating rows
        table_style = [
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternating rows and bold left column
        for i in range(len(extremes_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
        
        extremes_table.setStyle(TableStyle(table_style))
        story.append(KeepTogether([
            Paragraph("Trade Extremes", sub_heading_style),
            Spacer(1, 0.15 * inch),
            extremes_table
        ]))
        story.append(Spacer(1, 0.3 * inch))
    
    # Per-ticker stats
    if data.per_ticker_stats:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        ticker_data = [["Ticker", "Trades", "Win Rate", "Net PnL", "Avg PnL/Trade"]]
        ticker_pnl_values = []  # Track for coloring
        
        for idx, ticker_stat in enumerate(data.per_ticker_stats[:10], start=1):
            net_pnl = ticker_stat.get("netPnl", 0)
            avg_pnl = ticker_stat.get("avgPnlPerTrade", 0)
            
            ticker_pnl_values.append((idx, 3, net_pnl))  # Row, col 3 (Net PnL)
            ticker_pnl_values.append((idx, 4, avg_pnl))  # Row, col 4 (Avg PnL)
            
            ticker_data.append([
                ticker_stat["ticker"],
                str(ticker_stat["tradeCount"]),
                _format_percentage(ticker_stat.get("winRate")),
                _format_currency(net_pnl),
                _format_currency(avg_pnl),
            ])
        
        # Convert table data to Paragraphs with color coding for P/L columns
        ticker_table_data = []
        for row_idx, row in enumerate(ticker_data):
            row_cells = []
            for col_idx, cell in enumerate(row):
                # Check if this is a P/L column (cols 3 and 4) and not header row
                if row_idx > 0 and col_idx in [3, 4]:
                    pnl_value = next((v for r, c, v in ticker_pnl_values if r == row_idx and c == col_idx), None)
                    if pnl_value is not None:
                        color_hex = "#10B981" if pnl_value > 0 else ("#EF4444" if pnl_value < 0 else "#F1F5F9")
                        colored_style = ParagraphStyle("ColoredBody", parent=body_style, textColor=HexColor(color_hex))
                        row_cells.append(Paragraph(str(cell), colored_style))
                    else:
                        row_cells.append(Paragraph(str(cell), body_style))
                else:
                    row_cells.append(Paragraph(str(cell), body_style))
            ticker_table_data.append(row_cells)
        
        ticker_table = Table(ticker_table_data, colWidths=[1.0 * inch, 0.8 * inch, 0.95 * inch, 1.15 * inch, 1.15 * inch])
        
        # Professional styling with alternating rows
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, 0), 1, RAGARD_ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternating rows and white text
        for i in range(1, len(ticker_table_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
        
        # Color P/L columns
        for row_idx, col_idx, pnl_value in ticker_pnl_values:
            color = RAGARD_SUCCESS if pnl_value > 0 else (RAGARD_DANGER if pnl_value < 0 else colors.white)
            table_style.append(("TEXTCOLOR", (col_idx, row_idx), (col_idx, row_idx), color))
        
        ticker_table.setStyle(TableStyle(table_style))
        story.append(KeepTogether([
            Paragraph("Top Tickers by Trade Count", sub_heading_style),
            Spacer(1, 0.15 * inch),
            ticker_table
        ]))
        story.append(Spacer(1, 0.3 * inch))
    
    # Holding period stats
    if data.holding_period_stats:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        holding_data = [["Holding Period", "Trades", "Win Rate"]]
        for bucket, stats in data.holding_period_stats.items():
            holding_data.append([
                bucket,
                str(stats["trades"]),
                _format_percentage(stats.get("winRate")),
            ])
        
        # Convert table data to Paragraphs for word wrapping
        holding_table_data = []
        for row in holding_data:
            holding_table_data.append([
                Paragraph(str(cell), body_style) if isinstance(cell, str) else cell
                for cell in row
            ])
        
        holding_table = Table(holding_table_data, colWidths=[1.6 * inch, 1.1 * inch, 1.1 * inch])
        
        # Professional styling
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, 0), 1, RAGARD_ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternating rows and white text
        for i in range(1, len(holding_table_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
        
        holding_table.setStyle(TableStyle(table_style))
        story.append(KeepTogether([
            Paragraph("Win Rate by Holding Period", sub_heading_style),
            Spacer(1, 0.15 * inch),
            holding_table
        ]))
        story.append(Spacer(1, 0.3 * inch))
    
    # Side distribution
    if data.long_count > 0 or data.short_count > 0:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        
        side_data = [
            ["Side", "Count"],
            ["Long", str(data.long_count)],
            ["Short", str(data.short_count)],
        ]
        
        # Convert table data to Paragraphs for word wrapping
        side_table_data = []
        for row in side_data:
            side_table_data.append([
                Paragraph(str(cell), body_style) if isinstance(cell, str) else cell
                for cell in row
            ])
        
        side_table = Table(side_table_data, colWidths=[2.3 * inch, 2.1 * inch])
        
        # Professional styling (header color matches other tables)
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),  # Body left
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, 0), 1, RAGARD_ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternating rows and white text, bold left column
        for i in range(1, len(side_table_data)):  # Start from 1 to skip header
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
            table_style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
        
        side_table.setStyle(TableStyle(table_style))
        story.append(KeepTogether([
            Paragraph("Position Distribution", sub_heading_style),
            Spacer(1, 0.15 * inch),
            side_table
        ]))
        story.append(Spacer(1, 0.3 * inch))
    
    # Visual Charts
    if data.cumulative_pnl_data:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        story.append(KeepTogether([
            Paragraph("Cumulative Realized P/L Over Time", sub_heading_style),
            Spacer(1, 0.15 * inch),
            ChartFlowable("cumulative_pnl", data.cumulative_pnl_data, width=6*inch, height=3*inch),
        ]))
        # Add caption
        caption_style = ParagraphStyle(
            "Caption",
            parent=styles["Normal"],
            fontSize=8,
            textColor=RAGARD_TEXT_SECONDARY,
            italic=True,
            alignment=TA_CENTER,
        )
        story.append(Spacer(1, 0.1 * inch))
        story.append(Paragraph("<i>Chart shows realized P/L from closed trades only (open positions not included)</i>", caption_style))
        story.append(Spacer(1, 0.3 * inch))
    
    if data.pnl_distribution:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        story.append(KeepTogether([
            Paragraph("PnL Distribution", sub_heading_style),
            Spacer(1, 0.15 * inch),
            ChartFlowable("pnl_distribution", data.pnl_distribution, width=6*inch, height=3*inch),
        ]))
        story.append(Spacer(1, 0.3 * inch))
    
    # Monthly Breakdown
    if data.monthly_breakdown:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        monthly_data = [["Month", "Trades", "Wins", "Losses", "Win\nRate", "Total\nPnL"]]
        monthly_pnl_values = []  # Track for coloring
        
        for idx, month in enumerate(data.monthly_breakdown, start=1):
            pnl = month["totalPnl"]
            monthly_pnl_values.append((idx, pnl))
            
            monthly_data.append([
                month["month"],
                str(month["trades"]),
                str(month["wins"]),
                str(month["losses"]),
                _format_percentage(month.get("winRate")),
                _format_currency(pnl),
            ])
        
        # Convert table data to Paragraphs with color coding for P/L column
        monthly_table_data = []
        for row_idx, row in enumerate(monthly_data):
            row_cells = []
            for col_idx, cell in enumerate(row):
                # Color the Total PnL column (col 5) for non-header rows
                if row_idx > 0 and col_idx == 5:
                    pnl_value = next((v for r, v in monthly_pnl_values if r == row_idx), None)
                    if pnl_value is not None:
                        color_hex = "#10B981" if pnl_value > 0 else ("#EF4444" if pnl_value < 0 else "#F1F5F9")
                        colored_style = ParagraphStyle("ColoredBody", parent=body_style, textColor=HexColor(color_hex))
                        row_cells.append(Paragraph(str(cell), colored_style))
                    else:
                        row_cells.append(Paragraph(str(cell), body_style))
                else:
                    row_cells.append(Paragraph(str(cell), body_style))
            monthly_table_data.append(row_cells)
        
        monthly_table = Table(monthly_table_data, colWidths=[1.2 * inch, 0.75 * inch, 0.65 * inch, 0.75 * inch, 0.85 * inch, 1.25 * inch])
        
        # Professional styling
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, 0), 1, RAGARD_ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternating rows and white text
        for i in range(1, len(monthly_table_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
        
        monthly_table.setStyle(TableStyle(table_style))
        story.append(KeepTogether([
            Paragraph("Monthly Performance", sub_heading_style),
            Spacer(1, 0.15 * inch),
            monthly_table
        ]))
        
        if data.best_month or data.worst_month:
            story.append(Spacer(1, 0.2 * inch))
            if data.best_month:
                story.append(Paragraph(f"Best Month: {data.best_month['month']} ({_format_currency(data.best_month['totalPnl'])})", body_style))
            if data.worst_month:
                story.append(Paragraph(f"Worst Month: {data.worst_month['month']} ({_format_currency(data.worst_month['totalPnl'])})", body_style))
        
        story.append(Spacer(1, 0.3 * inch))
    
    # Risk Metrics
    risk_data = []
    if data.max_drawdown is not None:
        risk_data.append(["Max Drawdown", _format_currency(data.max_drawdown)])
    if data.risk_reward_ratio is not None:
        risk_data.append(["Risk/Reward Ratio", f"{data.risk_reward_ratio:.2f}"])
    if data.avg_position_size is not None:
        risk_data.append(["Avg Position Size", _format_currency(data.avg_position_size)])
    if data.largest_position_size is not None:
        risk_data.append(["Largest Position", _format_currency(data.largest_position_size)])
    
    if risk_data:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        # Convert table data to Paragraphs for word wrapping
        risk_table_data = []
        for row in risk_data:
            risk_table_data.append([
                Paragraph(str(cell), body_style) if isinstance(cell, str) else cell
                for cell in row
            ])
        
        risk_table = Table(risk_table_data, colWidths=[2.3 * inch, 2.1 * inch])
        
        # Professional styling
        table_style = [
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternating rows and bold left column
        for i in range(len(risk_table_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
        
        risk_table.setStyle(TableStyle(table_style))
        
        risk_items = [
            Paragraph("Risk Metrics", sub_heading_style),
            Spacer(1, 0.15 * inch),
            risk_table
        ]
        story.append(KeepTogether(risk_items))
        story.append(Spacer(1, 0.3 * inch))
    
    # Exit Timing Analysis
    if data.winner_avg_holding_period is not None or data.loser_avg_holding_period is not None:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        exit_data = []
        if data.winner_avg_holding_period is not None:
            exit_data.append(["Avg Holding (Winners)", _format_holding_period(data.winner_avg_holding_period)])
        if data.loser_avg_holding_period is not None:
            exit_data.append(["Avg Holding (Losers)", _format_holding_period(data.loser_avg_holding_period)])
        
        if exit_data:
            # Convert table data to Paragraphs for word wrapping
            exit_table_data = []
            for row in exit_data:
                exit_table_data.append([
                    Paragraph(str(cell), body_style) if isinstance(cell, str) else cell
                    for cell in row
                ])
            
            exit_table = Table(exit_table_data, colWidths=[2.3 * inch, 2.1 * inch])
            
            # Professional styling
            table_style = [
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
            
            # Alternating rows and bold left column
            for i in range(len(exit_table_data)):
                if i % 2 == 0:
                    table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
                else:
                    table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
                table_style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
            
            exit_table.setStyle(TableStyle(table_style))
            story.append(KeepTogether([
                Paragraph("Exit Timing Analysis", sub_heading_style),
                Spacer(1, 0.15 * inch),
                exit_table
            ]))
            story.append(Spacer(1, 0.3 * inch))
    
    # Trading Velocity
    if data.trades_per_week is not None or data.trades_per_month is not None or data.most_active_period:
        sub_heading_style = ParagraphStyle(
            "SubHeading",
            parent=styles["Heading3"],
            fontSize=13,
            textColor=RAGARD_TEXT_PRIMARY,
            spaceBefore=0.2 * inch,
            spaceAfter=0.15 * inch,
        )
        velocity_data = []
        if data.trades_per_week is not None:
            velocity_data.append(["Trades per Week", f"{data.trades_per_week:.1f}"])
        if data.trades_per_month is not None:
            velocity_data.append(["Trades per Month", f"{data.trades_per_month:.1f}"])
        if data.most_active_period:
            velocity_data.append(["Most Active Day", data.most_active_period])
        
        if velocity_data:
            # Convert table data to Paragraphs for word wrapping
            velocity_table_data = []
            for row in velocity_data:
                velocity_table_data.append([
                    Paragraph(str(cell), body_style) if isinstance(cell, str) else cell
                    for cell in row
                ])
            
            velocity_table = Table(velocity_table_data, colWidths=[2.3 * inch, 2.1 * inch])
            
            # Professional styling
            table_style = [
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
            
            # Alternating rows and bold left column
            for i in range(len(velocity_table_data)):
                if i % 2 == 0:
                    table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
                else:
                    table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
                table_style.append(("FONTNAME", (0, i), (0, i), "Helvetica-Bold"))
            
            velocity_table.setStyle(TableStyle(table_style))
            story.append(KeepTogether([
                Paragraph("Trading Velocity", sub_heading_style),
                Spacer(1, 0.15 * inch),
                velocity_table
            ]))
            story.append(Spacer(1, 0.3 * inch))
    
    # Add Performance Analytics section analysis
    if narrative.performance_analytics_analysis:
        story.append(Spacer(1, 0.3 * inch))
        analysis_heading = ParagraphStyle(
            "AnalysisHeading",
            parent=styles["Normal"],
            fontSize=10,
            textColor=RAGARD_ACCENT,
            fontName="Helvetica-Bold",
            spaceAfter=0.1 * inch,
        )
        story.append(Paragraph("Analysis", analysis_heading))
        
        analysis_style = ParagraphStyle(
            "Analysis",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.white,
            leading=13,
            spaceAfter=0.2 * inch,
            italic=True,
        )
        story.append(Paragraph(narrative.performance_analytics_analysis, analysis_style))
    
    story.append(PageBreak())
    
    # ===== DEGEN MOMENTS =====
    if data.degen_trades:
        story.append(Paragraph("Biggest Moves - Realized P/L (Degen Moments)", heading_style))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph("Your highest absolute <b>realized</b> P/L trades (closed positions only) - the ones that made or broke you.", body_style))
        story.append(Spacer(1, 0.2 * inch))
        
        degen_data = [["Ticker", "Side", "Date", "Realized P/L"]]
        degen_pnl_values = []  # Track for coloring
        
        for idx, trade in enumerate(data.degen_trades[:10], start=1):
            entry_date = _format_date(trade.get("entry_time"))
            pnl = trade.get("realized_pnl", 0)
            degen_pnl_values.append((idx, pnl))
            
            degen_data.append([
                trade.get("ticker", ""),
                trade.get("side", "").upper(),
                entry_date[:10] if len(entry_date) > 10 else entry_date,
                _format_currency(pnl),
            ])
        
        # Convert table data to Paragraphs with color coding for P/L column
        degen_table_data = []
        for row_idx, row in enumerate(degen_data):
            row_cells = []
            for col_idx, cell in enumerate(row):
                # Color the Realized P/L column (col 3) for non-header rows
                if row_idx > 0 and col_idx == 3:
                    pnl_value = next((v for r, v in degen_pnl_values if r == row_idx), None)
                    if pnl_value is not None:
                        color_hex = "#10B981" if pnl_value > 0 else ("#EF4444" if pnl_value < 0 else "#F1F5F9")
                        colored_style = ParagraphStyle("ColoredBody", parent=body_style, textColor=HexColor(color_hex))
                        row_cells.append(Paragraph(str(cell), colored_style))
                    else:
                        row_cells.append(Paragraph(str(cell), body_style))
                else:
                    row_cells.append(Paragraph(str(cell), body_style))
            degen_table_data.append(row_cells)
        
        degen_table = Table(degen_table_data, colWidths=[1.1 * inch, 0.9 * inch, 1.3 * inch, 1.6 * inch])
        
        # Professional styling
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, 0), 1, RAGARD_ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        
        # Alternating rows and white text
        for i in range(1, len(degen_table_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
        
        # Color P/L column (last column)
        for row_idx, pnl_value in degen_pnl_values:
            color = RAGARD_SUCCESS if pnl_value > 0 else (RAGARD_DANGER if pnl_value < 0 else colors.white)
            table_style.append(("TEXTCOLOR", (3, row_idx), (3, row_idx), color))
        
        degen_table.setStyle(TableStyle(table_style))
        story.append(degen_table)
        # Add Score Breakdown section analysis
    if narrative.score_breakdown_analysis:
        story.append(Spacer(1, 0.3 * inch))
        analysis_heading = ParagraphStyle(
            "AnalysisHeading",
            parent=styles["Normal"],
            fontSize=10,
            textColor=RAGARD_ACCENT,
            fontName="Helvetica-Bold",
            spaceAfter=0.1 * inch,
        )
        story.append(Paragraph("Analysis", analysis_heading))
        
        analysis_style = ParagraphStyle(
            "Analysis",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.white,
            leading=13,
            spaceAfter=0.2 * inch,
            italic=True,
        )
        story.append(Paragraph(narrative.score_breakdown_analysis, analysis_style))
    
    story.append(PageBreak())
    
    # ===== SECTION 3: STYLE & BEHAVIOR =====
    story.append(Paragraph("How You Trade (According to Ragard)", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Style summary
    story.append(Paragraph(narrative.style_summary, body_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Strengths
    sub_heading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=RAGARD_SUCCESS,
        spaceBefore=0.2 * inch,
        spaceAfter=0.15 * inch,
    )
    story.append(KeepTogether([
        Paragraph("Strengths", sub_heading_style)
    ]))
    for strength in narrative.strengths:
        story.append(Paragraph(f"• {strength}", body_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Weaknesses
    sub_heading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=RAGARD_DANGER,
        spaceBefore=0.2 * inch,
        spaceAfter=0.15 * inch,
    )
    story.append(KeepTogether([
        Paragraph("Weaknesses", sub_heading_style)
    ]))
    for weakness in narrative.weaknesses:
        story.append(Paragraph(f"• {weakness}", body_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Behavioral patterns
    sub_heading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=RAGARD_ACCENT,
        spaceBefore=0.2 * inch,
        spaceAfter=0.15 * inch,
    )
    story.append(KeepTogether([
        Paragraph("Behavioral Patterns", sub_heading_style)
    ]))
    for pattern in narrative.behavioural_patterns:
        story.append(Paragraph(f"• {pattern}", body_style))
    
    # Add Style & Behavior section analysis
    if narrative.style_behavior_analysis:
        story.append(Spacer(1, 0.3 * inch))
        analysis_heading = ParagraphStyle(
            "AnalysisHeading",
            parent=styles["Normal"],
            fontSize=10,
            textColor=RAGARD_ACCENT,
            fontName="Helvetica-Bold",
            spaceAfter=0.1 * inch,
        )
        story.append(Paragraph("Analysis", analysis_heading))
        
        analysis_style = ParagraphStyle(
            "Analysis",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.white,
            leading=13,
            spaceAfter=0.2 * inch,
            italic=True,
        )
        story.append(Paragraph(narrative.style_behavior_analysis, analysis_style))
    
    story.append(PageBreak())
    
    # ===== SECTION 4: RECOMMENDATIONS & 30-DAY PLAN =====
    story.append(Paragraph("How to Level Up Your Trading", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # Recommendations
    sub_heading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=RAGARD_ACCENT,
        spaceBefore=0.2 * inch,
        spaceAfter=0.15 * inch,
    )
    story.append(KeepTogether([
        Paragraph("Ragard Recommendations", sub_heading_style)
    ]))
    for rec in narrative.recommendations:
        story.append(Paragraph(f"• {rec}", body_style))
    story.append(Spacer(1, 0.2 * inch))
    
    # 30-day plan
    sub_heading_style = ParagraphStyle(
        "SubHeading",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=RAGARD_ACCENT,
        spaceBefore=0.2 * inch,
        spaceAfter=0.15 * inch,
    )
    story.append(KeepTogether([
        Paragraph("Next 30 Days Game Plan", sub_heading_style)
    ]))
    for item in narrative.thirty_day_plan:
        story.append(Paragraph(f"• {item}", body_style))
    
    story.append(PageBreak())
    
    # ===== OPEN POSITIONS =====
    if data.open_positions_count > 0 and data.open_positions_list:
        story.append(Paragraph("Current Open Positions (Unrealized P/L)", heading_style))
        story.append(Spacer(1, 0.2 * inch))
        
        intro_text = (
            f"You have {data.open_positions_count} aggregated open position{'s' if data.open_positions_count != 1 else ''} "
            "(one row per ticker/side, not per individual buy). "
            "All P/L shown below is <b>UNREALIZED and ESTIMATED</b> based on current prices. "
            "Option values are approximated using intrinsic value only (no time value). "
            "These factor into your Regard Score."
        )
        story.append(Paragraph(intro_text, body_style))
        story.append(Spacer(1, 0.2 * inch))
        
        # Open positions table with non-breaking headers
        open_data = [["Ticker", "Side", "Qty", "Avg\nEntry $", "Current\n$", "Unrealized\nP/L", "Return\n%", "Days\nOpen"]]
        open_pnl_values = []  # Track for coloring
        
        for pos in data.open_positions_list[:20]:  # Show up to 20
            entry_time = pos.get("entry_time")
            days_held = "N/A"
            if entry_time:
                try:
                    from datetime import timezone
                    entry_dt = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
                    now_aware = datetime.now(timezone.utc)
                    days_held = str((now_aware - entry_dt).days)
                except Exception:
                    pass
            
            current_price = pos.get("current_price")
            unrealized_pnl = pos.get("unrealized_pnl")
            unrealized_return = pos.get("unrealized_return")
            
            # Format unrealized return as percentage with non-breaking space before %
            unreal_ret_str = "N/A"
            if unrealized_return is not None:
                # Use non-breaking space (Unicode \u00A0) before % to prevent wrapping
                unreal_ret_str = f"{unrealized_return * 100:+.1f}\u00A0%"
            
            # Track row for coloring (unrealized P/L and return %)
            open_pnl_values.append((len(open_data), 5, unrealized_pnl))
            open_pnl_values.append((len(open_data), 6, unrealized_return))
            
            open_data.append([
                pos.get("ticker", ""),
                pos.get("side", "").upper(),
                f"{pos.get('quantity', 0):.1f}",
                _format_currency(pos.get("entry_price")),
                _format_currency(current_price) if current_price else "N/A",
                _format_currency(unrealized_pnl) if unrealized_pnl is not None else "N/A",
                unreal_ret_str,
                days_held,
            ])
        
        # Convert to paragraphs with color coding for P/L and return columns
        open_table_data = []
        for row_idx, row in enumerate(open_data):
            row_cells = []
            for col_idx, cell in enumerate(row):
                # Color Unrealized P/L (col 5) and Return % (col 6) for non-header rows
                if row_idx > 0 and col_idx in [5, 6]:
                    value = next((v for r, c, v in open_pnl_values if r == row_idx and c == col_idx), None)
                    if value is not None:
                        color_hex = "#10B981" if value > 0 else ("#EF4444" if value < 0 else "#F1F5F9")
                        colored_style = ParagraphStyle("ColoredBody", parent=body_style, textColor=HexColor(color_hex))
                        row_cells.append(Paragraph(str(cell), colored_style))
                    else:
                        row_cells.append(Paragraph(str(cell), body_style))
                else:
                    row_cells.append(Paragraph(str(cell), body_style))
            open_table_data.append(row_cells)
        
        open_table = Table(open_table_data, colWidths=[0.8 * inch, 0.7 * inch, 0.5 * inch, 0.75 * inch, 0.75 * inch, 0.95 * inch, 0.7 * inch, 0.6 * inch])
        
        # Professional styling
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),  # Slightly smaller font for better fit
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), 1, RAGARD_ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("WORDWRAP", (0, 0), (-1, -1), False),  # Prevent word wrap
        ]
        
        # Alternating rows and white text
        for i in range(1, len(open_table_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
        
        open_table.setStyle(TableStyle(table_style))
        story.append(open_table)
        
        # Calculate totals
        story.append(Spacer(1, 0.15 * inch))
        
        # Count positions that could be priced vs N/A
        priceable = [p for p in data.open_positions_list if p.get("current_price") is not None]
        unpriceable = [p for p in data.open_positions_list if p.get("current_price") is None]
        
        if data.open_positions_unrealized_pnl is not None and priceable:
            total_style = ParagraphStyle(
                "OpenTotal",
                parent=styles["Normal"],
                fontSize=11,
                textColor=RAGARD_TEXT_PRIMARY,
                fontName="Helvetica-Bold",
            )
            story.append(Paragraph(
                f"<b>Total Unrealized P/L ({len(priceable)} priced position{'s' if len(priceable) != 1 else ''}):</b> {_format_currency(data.open_positions_unrealized_pnl)}",
                total_style
            ))
            
            # Show combined total
            if data.total_pnl is not None:
                combined_total = data.total_pnl + data.open_positions_unrealized_pnl
                story.append(Spacer(1, 0.1 * inch))
                combined_style = ParagraphStyle(
                    "CombinedTotal",
                    parent=styles["Normal"],
                    fontSize=11,
                    textColor=RAGARD_ACCENT,
                    fontName="Helvetica-Bold",
                )
                story.append(Paragraph(
                    f"<b>Total P/L (Realized + Unrealized):</b> {_format_currency(combined_total)}",
                    combined_style
                ))
        
        # Note about unpriceable positions
        if unpriceable:
            story.append(Spacer(1, 0.1 * inch))
            note_style = ParagraphStyle(
                "UnpriceableNote",
                parent=styles["Normal"],
                fontSize=8,
                textColor=RAGARD_TEXT_SECONDARY,
                italic=True,
            )
            story.append(Paragraph(
                f"<i>Note: {len(unpriceable)} position{'s' if len(unpriceable) != 1 else ''} could not be priced "
                f"(options, illiquid tickers, etc.) and show N/A. These are excluded from Unrealized P/L totals.</i>",
                note_style
            ))
        
        story.append(PageBreak())
    
    # ===== SECTION 5: TRADE APPENDIX =====
    story.append(Paragraph("Trade Appendix", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    if data.trade_list:
        # Limit to last 100 for readability
        display_trades = data.trade_list[-100:]
        
        trade_data = [["Date", "Ticker", "Side", "Qty", "Entry", "Exit", "PnL"]]
        trade_pnl_values = []  # Track for coloring
        
        for idx, trade in enumerate(display_trades, start=1):
            entry_date = _format_date(trade.get("entry_time"))
            side = trade.get("side", "").upper()
            # Normalize side display
            if side in ("SHORT", "SELL"):
                side_display = "SHORT"
            elif side in ("LONG", "BUY"):
                side_display = "LONG"
            else:
                side_display = side
            
            pnl = trade.get("realized_pnl", 0)
            trade_pnl_values.append((idx, pnl))
            
            # Format date as MM/DD/YYYY
            formatted_date = entry_date
            try:
                dt = datetime.fromisoformat(trade.get("entry_time").replace("Z", "+00:00"))
                formatted_date = dt.strftime("%m/%d/%Y")
            except Exception:
                formatted_date = entry_date[:10] if len(entry_date) > 10 else entry_date
            
            trade_data.append([
                formatted_date,
                trade.get("ticker", ""),
                side_display,
                str(int(trade.get("quantity", 0))),
                _format_currency(trade.get("entry_price")),
                _format_currency(trade.get("exit_price")),
                _format_currency(pnl),
            ])
        
        # Convert table data to Paragraphs with color coding for P/L column
        trade_table_data = []
        for row_idx, row in enumerate(trade_data):
            row_cells = []
            for col_idx, cell in enumerate(row):
                # Color the PnL column (col 6) for non-header rows
                if row_idx > 0 and col_idx == 6:
                    pnl_value = next((v for r, v in trade_pnl_values if r == row_idx), None)
                    if pnl_value is not None:
                        color_hex = "#10B981" if pnl_value > 0 else ("#EF4444" if pnl_value < 0 else "#F1F5F9")
                        colored_style = ParagraphStyle("ColoredBody", parent=body_style, textColor=HexColor(color_hex))
                        row_cells.append(Paragraph(str(cell), colored_style))
                    else:
                        row_cells.append(Paragraph(str(cell), body_style))
                else:
                    row_cells.append(Paragraph(str(cell), body_style))
            trade_table_data.append(row_cells)
        
        # Professional styling for trade table
        trade_table = Table(trade_table_data, colWidths=[0.9 * inch, 0.85 * inch, 0.75 * inch, 0.5 * inch, 0.8 * inch, 0.8 * inch, 0.9 * inch])
        
        table_style = [
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1E3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 1), (0, -1), "LEFT"),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),  # Slightly smaller for better fit
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("LINEBELOW", (0, 0), (-1, 0), 1, RAGARD_ACCENT),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("WORDWRAP", (0, 0), (-1, -1), False),  # Prevent word wrap
        ]
        
        # Alternating rows and white text
        for i in range(1, len(trade_table_data)):
            if i % 2 == 0:
                table_style.append(("BACKGROUND", (0, i), (-1, i), HexColor("#1A2332")))
            else:
                table_style.append(("BACKGROUND", (0, i), (-1, i), RAGARD_SURFACE))
            table_style.append(("TEXTCOLOR", (0, i), (-1, i), colors.white))
        
        trade_table.setStyle(TableStyle(table_style))
        story.append(trade_table)
        
        if len(data.trade_list) > 100:
            story.append(Spacer(1, 0.1 * inch))
            note_style = ParagraphStyle(
                "Note",
                parent=styles["Normal"],
                fontSize=8,
                textColor=RAGARD_TEXT_SECONDARY,
                italic=True,
            )
            story.append(Paragraph(f"Note: Only last 100 trades shown. Total trades: {len(data.trade_list)}", note_style))
    else:
        story.append(Paragraph("No trades available for display.", body_style))
    
    # ===== DISCLAIMER SECTION =====
    story.append(PageBreak())
    story.append(Paragraph("Disclaimer", heading_style))
    story.append(Spacer(1, 0.2 * inch))
    
    disclaimer_text = """
    <b>Data Accuracy & Limitations:</b><br/>
    This report is generated based on trade data provided to Ragard. While we strive for accuracy, 
    the data may contain errors, omissions, or be incomplete. Trade data is subject to the accuracy 
    of the source systems and may not reflect all trading activity.<br/><br/>
    
    <b>Not Financial Advice:</b><br/>
    This report is for informational and entertainment purposes only. It does not constitute financial, 
    investment, or trading advice. Past performance does not guarantee future results. Trading involves 
    substantial risk of loss and is not suitable for all investors.<br/><br/>
    
    <b>Regard Score:</b><br/>
    The Regard Score is a proprietary metric designed for entertainment and self-reflection. It is not 
    a measure of trading skill, financial success, or investment acumen. Higher scores do not indicate 
    better trading outcomes.<br/><br/>
    
    <b>AI-Generated Content:</b><br/>
    Narrative content, recommendations, and insights are generated using artificial intelligence and 
    may contain inaccuracies, biases, or inappropriate suggestions. Always consult with qualified 
    financial professionals before making trading decisions.<br/><br/>
    
    <b>Use at Your Own Risk:</b><br/>
    Ragard and its affiliates are not responsible for any trading decisions made based on this report. 
    You are solely responsible for your trading decisions and their outcomes.
    """
    
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=9,
        textColor=RAGARD_TEXT_SECONDARY,
        spaceAfter=8,
        leading=13,
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))
    
    # Build PDF
    doc.build(story, onFirstPage=_create_header_footer, onLaterPages=_create_header_footer)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes


async def generate_user_report_pdf(data: UserReportData, narrative: UserReportNarrative) -> bytes:
    """
    Generate a branded PDF report for the user (async wrapper).
    
    Runs the synchronous PDF generation in an executor to avoid blocking the event loop.
    
    Args:
        data: UserReportData with all metrics
        narrative: UserReportNarrative with AI-generated text
        
    Returns:
        PDF as bytes
    """
    import asyncio
    import concurrent.futures
    
    # Run PDF generation in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        pdf_bytes = await loop.run_in_executor(
            executor,
            _generate_user_report_pdf_sync,
            data,
            narrative
        )
    return pdf_bytes

