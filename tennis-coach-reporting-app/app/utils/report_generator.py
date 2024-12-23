from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from io import BytesIO
from datetime import datetime
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Image
from reportlab.lib.colors import HexColor, white, black, Color

def draw_rounded_rect(c, x, y, width, height, radius, fill_color=None, stroke_color=None):
    """Draw a rounded rectangle"""
    c.saveState()
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
    
    p = c.beginPath()
    p.moveTo(x + radius, y)
    p.lineTo(x + width - radius, y)
    p.arcTo(x + width - radius, y, x + width, y + radius, 0, 90)
    p.lineTo(x + width, y + height - radius)
    p.arcTo(x + width - radius, y + height - radius, x + width, y + height, 90, 90)
    p.lineTo(x + radius, y + height)
    p.arcTo(x, y + height - radius, x + radius, y + height, 180, 90)
    p.lineTo(x, y + radius)
    p.arcTo(x, y, x + radius, y + radius, 270, 90)
    p.close()
    c.drawPath(p, fill=1 if fill_color else 0, stroke=1 if stroke_color else 0)
    c.restoreState()

def draw_rating_value(c, x, y, value, field_type, options=None):
    """Draw different types of field values"""
    if field_type == 'RATING':
        max_rating = options.get('max', 5) if options else 5
        draw_rating_stars(c, x, y, int(value), max_rating=max_rating)
    else:
        # For text, number, select, and textarea
        c.drawString(x, y, str(value))

def draw_rating_stars(c, x, y, value, max_rating=5):
    """Draw star rating"""
    star_width = 15
    star_spacing = 20
    
    for i in range(max_rating):
        if i < value:
            c.setFillColor(HexColor('#fbbf24'))  # Gold color for filled stars
        else:
            c.setFillColor(HexColor('#e5e7eb'))  # Gray for empty stars
            
        c.circle(x + (i * star_spacing), y - 3, star_width/2, fill=1)

def create_single_report_pdf(report, output_buffer):
    """Create a professionally designed tennis report PDF"""
    c = canvas.Canvas(output_buffer, pagesize=A4)
    width, height = A4
    
    tennis_club_name = report.programme_player.tennis_club.name
    
    # Background
    c.setFillColor(HexColor('#F5F9FF'))
    c.rect(0, 0, width, height, fill=1)
    
    # Header section
    header_height = 180
    draw_rounded_rect(c, 30, height - header_height - 30, width - 60, header_height,
                     radius=10, fill_color=HexColor('#FFFFFF'))
    
    c.setFillColor(HexColor('#bae6fd'))
    c.circle(70, height - 80, 20, fill=1)
    
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 28)
    c.drawString(110, height - 90, "Tennis Progress Report")
    
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor('#64748b'))
    c.drawString(110, height - 110, tennis_club_name)
    c.drawString(110, height - 130, f"Term: {report.teaching_period.name}")
    
    # Player info section
    info_y = height - 250
    draw_rounded_rect(c, 30, info_y, width - 60, 80, radius=10,
                     fill_color=HexColor('#FFFFFF'))
    
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, info_y + 50, "Player Details")
    
    c.setFillColor(HexColor('#64748b'))
    c.setFont("Helvetica", 12)
    c.drawString(50, info_y + 25, f"Name: {report.student.name}")
    c.drawString(50, info_y + 5, f"Coach: {report.coach.name}")
    c.drawString(width/2, info_y + 25, f"Group: {report.tennis_group.name}")
    
    # Dynamic content sections
    current_y = info_y - 40
    
    for section in report.template.sections:
        current_y -= 40
        
        # Section header
        draw_rounded_rect(c, 30, current_y, width - 60, len(section.fields) * 40 + 60,
                         radius=10, fill_color=HexColor('#FFFFFF'))
        
        c.setFillColor(HexColor('#1e3a8a'))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, current_y + len(section.fields) * 40 + 30, section.name)
        
        # Fields
        field_y = current_y + len(section.fields) * 40
        for field in section.fields:
            value = report.content[section.name][field.name]
            
            c.setFillColor(HexColor('#64748b'))
            c.setFont("Helvetica", 12)
            c.drawString(50, field_y, f"{field.name}:")
            
            # Draw field value based on type
            if field.field_type == 'TEXTAREA':
                # Create a paragraph object for wrapped text
                style = ParagraphStyle(
                    'Field',
                    fontName='Helvetica',
                    fontSize=11,
                    textColor=HexColor('#64748b'),
                    leading=14
                )
                
                p = Paragraph(str(value), style)
                p.wrapOn(c, width - 200, 50)
                p.drawOn(c, 160, field_y - 20)
                field_y -= 60
            else:
                draw_rating_value(c, 160, field_y, value, field.field_type, field.options)
                field_y -= 30
        
        current_y -= len(section.fields) * 40
    
    # Footer
    c.setFillColor(HexColor('#64748b'))
    c.setFont("Helvetica", 10)
    current_date = datetime.now().strftime('%B %d, %Y')
    c.drawString(50, 30, f"Report generated on {current_date}")
    c.drawString(width - 200, 30, tennis_club_name)