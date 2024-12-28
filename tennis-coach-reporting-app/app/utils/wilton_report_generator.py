from flask import current_app
from app import create_app, db
from app.models import Report, TeachingPeriod
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import os
import json
import random
from random import uniform
from datetime import datetime
from reportlab.lib.colors import Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

class EnhancedWiltonReportGenerator:
    def __init__(self, config_path):
        """Initialize the report generator with configuration."""
        print(f"Loading config from: {config_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Config file not found at: {config_path}\n"
                f"Current directory: {os.getcwd()}\n"
                f"Directory contents: {os.listdir(os.path.dirname(config_path))}"
            )
            
        with open(config_path, 'r') as f:
            self.config = json.load(f)
       
        # Get base directory for fonts
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fonts_dir = os.path.join(base_dir, 'static', 'fonts')
        
        # Register handwriting font
        try:
            pdfmetrics.registerFont(TTFont('Handwriting', os.path.join(fonts_dir, 'caveat.ttf')))
            self.font_name = 'Handwriting'
        except:
            print("Warning: Handwriting font not found, falling back to Helvetica")
            self.font_name = 'Helvetica-Bold'
            
    def get_template_path(self, group_name):
        """Get the correct template path based on group name."""
        # Convert group name to lowercase and remove spaces for filename
        template_name = f"wilton_{group_name.lower().replace(' ', '_')}_report.pdf"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_dir, 'app', 'static', 'pdf_templates', template_name)
        
    def get_group_config(self, group_name):
        """Get the configuration for a specific group."""
        if group_name not in self.config:
            raise ValueError(f"No configuration found for group: {group_name}")
        return self.config[group_name]
        
    def draw_diagonal_text(self, c, text, x, y, angle=23):
        """Draw text at a specified angle with handwriting style."""
        c.saveState()
        c.translate(x, y)
        c.rotate(angle)
        
        # Base font size with slight variation
        base_size = 14
        font_size = base_size + uniform(-0.5, 0.5)
        
        c.setFont(self.font_name, font_size)
        
        # Add slight random rotation for each character
        chars = list(text)
        current_x = 0
        for char in chars:
            char_angle = uniform(-2, 2)  # Slight random rotation
            c.saveState()
            c.rotate(char_angle)
            c.drawString(current_x, uniform(-0.5, 0.5), char)  # Slight vertical variation
            c.restoreState()
            current_x += c.stringWidth(char, self.font_name, font_size) * 0.95  # Slightly tighter spacing
            
        c.restoreState()

    def draw_checkbox(self, canvas, x, y, checked=False, size=8):
        """Draw a more natural-looking checkbox tick with a handwriting style and debug font usage."""
        if checked:
            canvas.saveState()

            # Debugging: Check and set the custom font
            try:
                canvas.setFont(self.font_name, size)
            except Exception as e:
                canvas.setFont('Helvetica', size)

            # Handwritten-style tick path with minor randomness
            
            tick_color = Color(0, 0, 0, alpha=0.8)  # Slightly transparent black
            canvas.setStrokeColor(tick_color)
            canvas.setLineWidth(0.8)  # Thinner line for a more natural look

            # Add randomness to mimic handwriting
            def jitter(value, max_jitter=0.5):
                return value + random.uniform(-max_jitter, max_jitter)

            # Draw a tick path with irregularities
            p = canvas.beginPath()
            p.moveTo(jitter(x - size / 2), jitter(y - size / 4))
            p.curveTo(
                jitter(x - size / 3), jitter(y - size / 3),  # Control point 1
                jitter(x - size / 4), jitter(y - size / 2),  # Control point 2
                jitter(x - size / 6), jitter(y - size / 2)   # End point of the first curve
            )
            p.curveTo(
                jitter(x), jitter(y - size / 3),             # Control point 1
                jitter(x + size / 3), jitter(y + size / 3),  # Control point 2
                jitter(x + size / 2), jitter(y + size / 2)   # End point
            )
            canvas.drawPath(p)

            # Optionally, use a handwritten tick symbol
            label_offset = size  # Offset for text next to the checkbox
            canvas.drawString(x + label_offset, y, "✓")  # Ensure font is handwriting-style

            canvas.restoreState()

    def generate_page_overlay(self, data, config, page_num):
        """Generate a single page overlay."""
        packet = BytesIO()
        c = canvas.Canvas(packet, pagesize=A4)
        c.setFont("Helvetica-BoldOblique", 12)
        
        if page_num == 1:
            # Front page - add diagonal text fields
            coords = config.get('page1', {})
            
            # Only draw fields that exist in both config and data
            field_mappings = {
                'player_name': 'player_name',
                'coach_name': 'coach_name',
                'term': 'term',
                'group': 'group'
            }
            
            for field, data_key in field_mappings.items():
                if field in coords and data_key in data:
                    self.draw_diagonal_text(c, data[data_key], 
                                         coords[field][0], 
                                         coords[field][1])
            
        elif page_num == 2:
            # Report card page - add checkboxes only if sections exist
            sections = config.get('page2', {}).get('sections', {})
            content = data.get('content', {})
            
            # Process each section that exists in both config and content
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
            
            # Add group recommendation checkbox only if it exists in config
            rec_coords = config.get('page2', {}).get('group_recommendation')
            if rec_coords and 'group_recommendation' in data:
                if data['group_recommendation'] == 'Red' and 'red_x' in rec_coords:
                    self.draw_checkbox(c, rec_coords['red_x'], rec_coords['y'], True)
                elif data['group_recommendation'] == 'Orange' and 'orange_x' in rec_coords:
                    self.draw_checkbox(c, rec_coords['orange_x'], rec_coords['y'], True)
        
        c.save()
        packet.seek(0)
        return PdfReader(packet)

    def generate_report(self, template_path, output_path, data):
        """Generate a filled report PDF."""
        # Get group configuration
        group_config = self.get_group_config(data['group'])
        
        # Read the template
        template = PdfReader(open(template_path, "rb"))
        output = PdfWriter()
        
        # Process each page
        for page_num in range(len(template.pages)):
            # Get template page
            template_page = template.pages[page_num]
            
            # Generate and merge overlay
            overlay = self.generate_page_overlay(data, group_config, page_num + 1)
            template_page.merge_page(overlay.pages[0])
            
            # Add the merged page to output
            output.add_page(template_page)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Write the output PDF
        with open(output_path, "wb") as output_file:
            output.write(output_file)

    @classmethod
    def batch_generate_reports(cls, period_id, config_path=None):
        """Generate reports for all completed reports in a teaching period."""
        if config_path is None:
            # Fix path resolution to look in app/utils instead of utils
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'utils', 'wilton_group_config.json')
        
        generator = cls(config_path)
        
        # Get all completed reports for the period with related data
        reports = Report.query.filter_by(teaching_period_id=period_id)\
            .join(Report.programme_player)\
            .all()
        
        if not reports:
            return {
                'success': 0,
                'errors': 0,
                'error_details': ['No reports found for this period'],
                'output_directory': None
            }

        # Get period name for the main folder
        period_name = reports[0].teaching_period.name.replace(' ', '_').lower()
        
        # Set up base output directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reports_dir = os.path.join(base_dir, 'instance', 'reports')
        period_dir = os.path.join(reports_dir, f'reports-{period_name}')
        
        generated_reports = []
        errors = []
        
        for report in reports:
            try:
                # Get template path for this group
                template_path = generator.get_template_path(report.tennis_group.name)
                
                if not os.path.exists(template_path):
                    errors.append(f"Template not found for group: {report.tennis_group.name}")
                    continue
                
                # Create group-specific directory with time slot
                group_name = report.tennis_group.name.replace(' ', '_').lower()
                time_slot = ""
                if report.programme_player and report.programme_player.group_time:
                    time = report.programme_player.group_time
                    time_slot = f"{time.start_time.strftime('%I%M%p')}_{time.end_time.strftime('%I%M%p')}".lower()
                    group_dir = f"{group_name}_{time_slot}_reports"
                else:
                    group_dir = f"{group_name}_reports"
                
                full_group_dir = os.path.join(period_dir, group_dir)
                os.makedirs(full_group_dir, exist_ok=True)
                
                # Prepare output path with standardized naming
                student_name = report.student.name.replace(' ', '_').lower()
                term_name = report.teaching_period.name.replace(' ', '_').lower()
                filename = f"{student_name}_{group_name}_{term_name}_report.pdf"
                output_path = os.path.join(full_group_dir, filename)
                
                # Prepare report data
                data = {
                    'player_name': report.student.name,
                    'coach_name': report.coach.name,
                    'term': report.teaching_period.name,
                    'group': report.tennis_group.name,
                    'content': report.content,
                    'group_recommendation': 'Red' if 'Red' in report.recommended_group.name else 'Orange'
                }
                
                # Generate the report
                generator.generate_report(template_path, output_path, data)
                generated_reports.append(output_path)
                
            except Exception as e:
                errors.append(f"Error generating report for {report.student.name}: {str(e)}")
                
        return {
            'success': len(generated_reports),
            'errors': len(errors),
            'error_details': errors,
            'output_directory': output_path
        }

    @classmethod
    def generate_single_report(cls, report_id, output_dir=None, config_path=None):
        """Generate a report for a single specific report ID."""
        if config_path is None:
            # Fix path resolution to look in app/utils
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'app', 'utils', 'wilton_group_config.json')
            
        generator = cls(config_path)
        
        # Get the report
        report = Report.query.get(report_id)
        if not report:
            raise ValueError(f"Report not found with ID: {report_id}")
            
        # Set up output directory
        if output_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join(base_dir, 'instance', 'generated_reports', timestamp)
            
        os.makedirs(output_dir, exist_ok=True)
        
        # Get template path
        template_path = generator.get_template_path(report.tennis_group.name)
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found for group: {report.tennis_group.name}")
            
        # Prepare output path
        filename = f"{report.student.name}_{report.tennis_group.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join(output_dir, filename)
        
        # Prepare report data
        data = {
            'player_name': report.student.name,
            'coach_name': report.coach.name,
            'term': report.teaching_period.name,
            'group': report.tennis_group.name,
            'content': report.content,
            'group_recommendation': 'Red' if 'Red' in report.recommended_group.name else 'Orange'
        }
        
        # Generate the report
        generator.generate_report(template_path, output_path, data)
        
        return {
            'success': True,
            'output_path': output_path,
            'report_data': data
        }

def main():
    """Main function to test report generation"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if a specific report ID was provided as command line argument
            import sys
            if len(sys.argv) > 1 and sys.argv[1].isdigit():
                report_id = int(sys.argv[1])
                print(f"\nGenerating single report for ID: {report_id}")
                
                try:
                    result = EnhancedWiltonReportGenerator.generate_single_report(report_id)
                    print("\nReport generation complete!")
                    print(f"Report saved to: {result['output_path']}")
                    print("\nReport details:")
                    for key, value in result['report_data'].items():
                        if key != 'content':  # Skip printing the full content
                            print(f"{key}: {value}")
                    
                except Exception as e:
                    print(f"Error generating report: {str(e)}")
                    traceback.print_exc()
                    return
                    
            else:
                # Get the most recent teaching period
                period = TeachingPeriod.query.order_by(TeachingPeriod.start_date.desc()).first()
            if not period:
                print("Error: No teaching periods found")
                return
                
            print(f"\nGenerating reports for period: {period.name}")
            
            # Generate reports
            results = EnhancedWiltonReportGenerator.batch_generate_reports(period.id)
            
            print(f"\nReport generation complete!")
            print(f"Successfully generated: {results['success']} reports")
            print(f"Errors encountered: {results['errors']}")
            
            if results['errors'] > 0:
                print("\nError details:")
                for error in results['error_details']:
                    print(f"- {error}")
                    
            print(f"\nReports saved to: {results['output_directory']}")
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()