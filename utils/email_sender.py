import os
import logging
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId, Email,
    HtmlContent,Bcc
)

bcc_email = "testing.ocena@gmail.com"

def send_offer_letter_email(to_email, student_name, pdf_bytes, reference_number):
    """
    Send an email with the offer letter attached to the student.
    
    Args:
        to_email (str): Recipient email address
        student_name (str): Name of the student
        pdf_bytes (bytes): PDF content as bytes
        reference_number (str): Reference number for tracking
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Get API key from environment
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logging.error("SendGrid API key not found in environment variables")
            return False

        # Create the email
        from_email = os.environ.get('SENDER_EMAIL', 'admissions@rayatbahra.com')
        from_name = os.environ.get('SENDER_NAME', 'Rayat Bahra University Admissions')
        
        # Create HTML content
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
                
                    <h2 style="color: #003366; text-align: center;">Congratulations, {student_name}!</h2>
                    <p style="font-size: 16px; line-height: 1.5;">We are pleased to inform you that your application to Rayat Bahra University has been successful.</p>
                    <p style="font-size: 16px; line-height: 1.5;">Attached to this email is your official offer letter containing all the details about your program, fees, and next steps.</p>
                    <p style="font-size: 16px; line-height: 1.5;">Please review the attached document carefully and confirm your acceptance by replying to this email.</p>
                    <p style="font-size: 16px; line-height: 1.5;">If you have any questions or require further assistance, please do not hesitate to contact our admissions team.</p>
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <p style="font-size: 14px; color: #666;">Reference Number: {reference_number}</p>
                        <p style="font-size: 14px; color: #666;">Rayat Bahra University<br>
                        Admissions Office<br>
                        Email: admissions@uniportal.co.in<br>
                        Phone: +91-98759 30083</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message = Mail(
            from_email=Email(from_email, from_name),
            to_emails=to_email,
            bcc_emails=[bcc_email],
            subject=f"Congratulations! Your Offer Letter from Rayat Bahra University (Ref: {reference_number})",
            html_content=HtmlContent(html_content)
        )

        # Attach the PDF
        encoded_file = base64.b64encode(pdf_bytes).decode()
        
        attachment = Attachment()
        attachment.file_content = FileContent(encoded_file)
        attachment.file_type = FileType('application/pdf')
        attachment.file_name = FileName(f"Offer_Letter_{student_name.replace(' ', '_')}.pdf")
        attachment.disposition = Disposition('attachment')
        attachment.content_id = ContentId('Offer Letter')
        
        message.attachment = attachment

        # Send the email
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Check response for success (typically 202 for SendGrid)
        status_code = response.status_code
        if 200 <= status_code < 300:
            logging.info(f"Email sent successfully to {to_email}, status code: {status_code}")
            return True
        else:
            logging.error(f"Failed to send email to {to_email}, status code: {status_code}")
            return False
    
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return False

def send_bulk_emails(students_data, pdf_files, reference_numbers):
    """
    Send emails to multiple students.
    
    Args:
        students_data (list): List of student data dictionaries
        pdf_files (list): List of PDF bytes corresponding to each student
        reference_numbers (list): List of reference numbers
        
    Returns:
        dict: Summary of sent emails with success/failure status
    """
    results = {
        'total': len(students_data),
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for student, pdf_bytes, ref_num in zip(students_data, pdf_files, reference_numbers):
        sent = send_offer_letter_email(
            student['email'],
            student['name'],
            pdf_bytes,
            ref_num
        )
        
        status = 'sent' if sent else 'failed'
        results['details'].append({
            'name': student['name'],
            'email': student['email'],
            'status': status
        })
        
        if sent:
            results['success'] += 1
        else:
            results['failed'] += 1
    
    return results