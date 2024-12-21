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
    
    # Create the rounded rectangle path
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

def draw_rating_stars(c, x, y, rating, max_rating=5, star_size=12):
    """Draw star rating"""
    c.saveState()
    
    # Full star in gold
    full_star_path = c.beginPath()
    full_star_path.moveTo(star_size/2, 0)
    for i in range(5):
        full_star_path.lineTo(star_size/2 * (1 + 0.9 * (i % 2) * (2 - (i > 2))), 
                            star_size/2 * (0.3 + 0.9 * ((i + 1) % 2)))
    full_star_path.close()
    
    for i in range(max_rating):
        c.saveState()
        c.translate(x + i * (star_size + 2), y)
        if i < rating:
            c.setFillColor(HexColor('#FFD700'))  # Gold color
        else:
            c.setFillColor(HexColor('#D3D3D3'))  # Light gray
        c.drawPath(full_star_path, fill=1)
        c.restoreState()
    
    c.restoreState()

def create_single_report_pdf(report, output_buffer):
    """Create a professionally designed tennis report PDF"""
    c = canvas.Canvas(output_buffer, pagesize=A4)
    width, height = A4
    
    # Get tennis club name from programme_player
    tennis_club_name = report.programme_player.tennis_club.name
    
    # Background
    c.setFillColor(HexColor('#F5F9FF'))  # Light blue background
    c.rect(0, 0, width, height, fill=1)
    
    # Header section with tennis club info
    header_height = 180
    draw_rounded_rect(c, 30, height - header_height - 30, width - 60, header_height,
                     radius=10, fill_color=HexColor('#FFFFFF'))
    
    # Tennis ball icon
    c.setFillColor(HexColor('#bae6fd'))  # Light blue
    c.circle(70, height - 80, 20, fill=1)
    
    # Header text
    c.setFillColor(HexColor('#1e3a8a'))  # Dark blue
    c.setFont("Helvetica-Bold", 28)
    c.drawString(110, height - 90, "Tennis Progress Report")
    
    # Club info
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor('#64748b'))  # Slate gray
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
    
    # Skills assessment section
    skills_y = info_y - 220
    draw_rounded_rect(c, 30, skills_y, width - 60, 180, radius=10,
                     fill_color=HexColor('#FFFFFF'))
    
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, skills_y + 150, "Skills Assessment")
    
    # Draw assessment items with visual ratings
    metrics = [
        ("Forehand", report.forehand),
        ("Backhand", report.backhand),
        ("Movement", report.movement)
    ]
    
    current_y = skills_y + 110
    for metric, value in metrics:
        # Metric label
        c.setFillColor(HexColor('#64748b'))
        c.setFont("Helvetica", 12)
        c.drawString(50, current_y, f"{metric}:")
        
        # Create a rating indicator
        draw_rounded_rect(c, 150, current_y - 5, 300, 25, radius=5,
                         fill_color=HexColor('#f1f5f9'))
        c.setFillColor(HexColor('#1e3a8a'))
        c.setFont("Helvetica", 11)
        c.drawString(160, current_y, value)
        current_y -= 30
    
    # Overall rating
    c.setFillColor(HexColor('#64748b'))
    c.drawString(50, current_y, "Overall Rating:")
    draw_rating_stars(c, 150, current_y - 3, report.overall_rating)
    
    # Recommendation section
    rec_y = skills_y - 100
    draw_rounded_rect(c, 30, rec_y, width - 60, 60, radius=10,
                     fill_color=HexColor('#FFFFFF'))
    
    c.setFillColor(HexColor('#1e3a8a'))
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, rec_y + 35, "Next Term Recommendation")
    
    c.setFillColor(HexColor('#64748b'))
    c.setFont("Helvetica", 12)
    c.drawString(50, rec_y + 10, report.next_group_recommendation)
    
    # Notes section
    if report.notes:
        notes_y = rec_y - 120
        draw_rounded_rect(c, 30, notes_y, width - 60, 100, radius=10,
                         fill_color=HexColor('#FFFFFF'))
        
        c.setFillColor(HexColor('#1e3a8a'))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, notes_y + 70, "Coach's Notes")
        
        # Create a paragraph object for wrapped text
        style = ParagraphStyle(
            'Notes',
            fontName='Helvetica',
            fontSize=11,
            textColor=HexColor('#64748b'),
            leading=14
        )
        
        p = Paragraph(report.notes, style)
        p.wrapOn(c, width - 120, 50)  # Wrap text in available space
        p.drawOn(c, 50, notes_y + 10)
    
    # Footer
    c.setFillColor(HexColor('#64748b'))
    c.setFont("Helvetica", 10)
    current_date = datetime.now().strftime('%B %d, %Y')
    c.drawString(50, 30, f"Report generated on {current_date}")
    c.drawString(width - 200, 30, tennis_club_name)
    
    c.save()
    output_buffer.seek(0)