from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from io import BytesIO
import os

class WiltonReportGenerator:
    def __init__(self, template_path):
        """Initialize the report generator with the template path."""
        self.template_path = template_path
        
        # Define coordinates for each field (x, y) for both pages
        self.coordinates = {
            # Page 1 coordinates (front page)
            'page1': {
                'player_name': (250, 205), 
                'coach_name': (250, 162), 
                'term': (250, 127),   
                'group': (400, 193),
            },
            
           # Page 2 coordinates (report card)
            'page2': {
                # Section coordinates with their checkboxes
                'sections': {
                    'RULES OF TENNIS': {
                        'start_y': 575,
                        'spacing': 14,
                        'yes_x': 385,
                        'nearly_x': 405,
                        'not_yet_x': 425
                    },
                    'RACKET SKILLS': {
                        'start_y': 530,
                        'spacing': 14,
                        'yes_x': 385,
                        'nearly_x': 405,
                        'not_yet_x': 425
                    },
                    'THROWING AND CATCHING SKILLS': {
                        'start_y': 490,
                        'spacing': 14,
                        'yes_x': 385,
                        'nearly_x': 405,
                        'not_yet_x': 425
                    },
                    'GROUNDSTROKES': {
                        'start_y': 445,
                        'spacing': 14,
                        'yes_x': 385,
                        'nearly_x': 405,
                        'not_yet_x': 425
                    },
                    'SERVE': {
                        'start_y': 330,
                        'spacing': 14,
                        'yes_x': 385,
                        'nearly_x': 405,
                        'not_yet_x': 425
                    },
                    'RALLYING': {
                        'start_y': 265,
                        'spacing': 15,
                        'yes_x': 385,
                        'nearly_x': 405,
                        'not_yet_x': 425
                    },
                    'COMPETITION': {
                        'start_y': 175,
                        'spacing': 15,
                        'yes_x': 385,
                        'nearly_x': 405,
                        'not_yet_x': 425
                    }
                },

                'group_recommendation': {
                    'red_x': 338,
                    'orange_x': 418,
                    'y': 155
                }
            }
        }

    def draw_diagonal_text(self, c, text, x, y, angle=23):
        """Draw text at a specified angle."""
        c.saveState()
        c.translate(x, y)
        c.rotate(angle)
        c.setFont("Helvetica-BoldOblique", 12)  # Use a handwriting-style font
        c.drawString(0, 0, text)
        c.restoreState()

    def draw_checkbox(self, canvas, x, y, checked=False, size=8):
        """Draw a checkbox at the specified coordinates with a more handwritten-like tick."""
        if checked:
            canvas.setStrokeColorRGB(0, 0, 0)  # Set stroke color to black
            canvas.setLineWidth(1)  # Slightly reduce line width for a more hand-drawn feel
            # Draw a tick mark (✓) with simple strokes
            canvas.line(x - size/2, y - size/4, x - size/4, y - size/2)
            canvas.line(x - size/4, y - size/2, x + size/2, y + size/2)

    def generate_overlay(self, data, page_num):
        """Generate a single page overlay."""
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)
        c.setFont("Helvetica-BoldOblique", 12)  # Apply the handwritten font
        
        if page_num == 1:
            # Front page - add diagonal text fields
            coords = self.coordinates['page1']
            
            # Draw each text field at 45 degrees
            self.draw_diagonal_text(c, data['player_name'], coords['player_name'][0], coords['player_name'][1])
            self.draw_diagonal_text(c, data['coach_name'], coords['coach_name'][0], coords['coach_name'][1])
            self.draw_diagonal_text(c, data['term'], coords['term'][0], coords['term'][1])
            self.draw_diagonal_text(c, data['group'], coords['group'][0], coords['group'][1])
            
        elif page_num == 2:
            # Report card page - add checkboxes
            sections = self.coordinates['page2']['sections']
            content = data['content']
            
            # Process each section
            for section_name, section_coords in sections.items():
                if section_name in content:
                    y_pos = section_coords['start_y']
                    
                    # Process each question in the section
                    for value in content[section_name].values():
                        if value == 'Yes':
                            self.draw_checkbox(c, section_coords['yes_x'], y_pos, True)
                        elif value == 'Nearly':
                            self.draw_checkbox(c, section_coords['nearly_x'], y_pos, True)
                        elif value == 'Not Yet':
                            self.draw_checkbox(c, section_coords['not_yet_x'], y_pos, True)
                        y_pos -= section_coords['spacing']
            
            # Add group recommendation checkbox
            rec_coords = self.coordinates['page2']['group_recommendation']
            if data['group_recommendation'] == 'Red':
                self.draw_checkbox(c, rec_coords['red_x'], rec_coords['y'], True)
            elif data['group_recommendation'] == 'Orange':
                self.draw_checkbox(c, rec_coords['orange_x'], rec_coords['y'], True)
        
        c.save()
        packet.seek(0)
        return PdfReader(packet)

    def generate_report(self, output_path, data):
        """Generate a filled report PDF."""
        # Read the template
        template = PdfReader(open(self.template_path, "rb"))
        output = PdfWriter()
        
        # Process each page
        for page_num in range(len(template.pages)):
            # Get template page
            template_page = template.pages[page_num]
            
            # Generate and merge overlay
            overlay = self.generate_overlay(data, page_num + 1)
            template_page.merge_page(overlay.pages[0])
            
            # Add the merged page to output
            output.add_page(template_page)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the output PDF
        with open(output_path, "wb") as output_file:
            output.write(output_file)

    @classmethod
    def generate_report_from_db(cls, template_path, output_path, report_data):
        """Generate a report from database data."""
        # Transform database data into the format needed for report generation
        data = {
            'player_name': report_data.student.name,
            'coach_name': report_data.coach.name,
            'term': report_data.teaching_period.name,
            'group': report_data.tennis_group.name,
            'content': report_data.content,
            'group_recommendation': 'Red' if 'Red' in report_data.recommended_group.name else 'Orange' if 'Orange' in report_data.recommended_group.name else '' 
        }
        print(data)
        # Generate the report
        generator = cls(template_path)
        generator.generate_report(output_path, data)
