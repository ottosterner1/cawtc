import boto3
from botocore.exceptions import ClientError
from flask import current_app
import logging
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from app.utils.report_generator import create_single_report_pdf
from io import BytesIO
import traceback

class EmailService:
    def __init__(self):
        self.region = current_app.config['AWS_SES_REGION']
        self.ses_client = boto3.client(
            'ses',
            region_name=self.region,
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY']
        )
        self.sender = current_app.config['AWS_SES_SENDER']

    def _create_raw_email_with_attachment(self, recipient, subject, message, pdf_data, student_name):
        """Create a raw email with PDF attachment"""
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = recipient

        # Add the message
        text_part = MIMEText(message, 'plain', 'utf-8')
        msg.attach(text_part)

        # Add the PDF attachment
        pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
        pdf_attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=f'{student_name}_Tennis_Report.pdf'
        )
        msg.attach(pdf_attachment)

        return msg.as_string()

    def send_reports_batch(self, reports, subject, message):
        """Send batch of reports with PDF attachments"""
        success_count = 0
        error_count = 0
        errors = []

        for report in reports:
            try:
                if not report.student.contact_email:
                    error_count += 1
                    errors.append(f"No email for student: {report.student.name}")
                    continue

                # Generate PDF
                pdf_buffer = BytesIO()
                create_single_report_pdf(report, pdf_buffer)
                pdf_buffer.seek(0)
                pdf_data = pdf_buffer.getvalue()

                # Create raw email with attachment
                raw_email = self._create_raw_email_with_attachment(
                    recipient=report.student.contact_email,
                    subject=subject,
                    message=message,
                    pdf_data=pdf_data,
                    student_name=report.student.name
                )

                # Send email
                self.ses_client.send_raw_email(
                    Source=self.sender,
                    RawMessage={'Data': raw_email}
                )

                # Update report status
                if hasattr(report, 'email_sent'):
                    report.email_sent = True
                    report.email_sent_at = datetime.now(timezone.utc)

                success_count += 1
                
            except ClientError as e:
                error_count += 1
                error_msg = f"Failed to send to {report.student.name}: {str(e)}"
                errors.append(error_msg)
                logging.error(error_msg)
                logging.error(traceback.format_exc())
                
            except Exception as e:
                error_count += 1
                error_msg = f"Unexpected error for {report.student.name}: {str(e)}"
                errors.append(error_msg)
                logging.error(error_msg)
                logging.error(traceback.format_exc())

        return success_count, error_count, errors
    
    def send_accreditation_reminder(self, email, coach_name, expiring_accreditations):
        subject = "LTA Accreditation Reminder"
        
        # Create the message body
        message = f"Dear {coach_name},\n\n"
        message += "This is a reminder about your upcoming accreditation expiries:\n\n"
        
        for accred_type, days in expiring_accreditations:
            if days < 0:
                message += f"- Your {accred_type} expired {abs(days)} days ago\n"
            else:
                message += f"- Your {accred_type} will expire in {days} days\n"
        
        message += "\nPlease ensure you renew these accreditations before they expire."
        
        # Send the email using your existing email sending mechanism
        self.send_email(email, subject, message)