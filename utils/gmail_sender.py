import os
import logging
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication



# Gmail SMTP settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "admissions@uniportal.co.in"
SMTP_PASSWORD = "nynpjpzwmuqrehbh"

def send_offer_letter_email(to_email, student_name, pdf_bytes, reference_number):
    """
    Send an email with the offer letter attached to the student using Gmail SMTP.
    
    Args:
        to_email (str): Recipient email address
        student_name (str): Name of the student
        pdf_bytes (bytes): PDF content as bytes
        reference_number (str): Reference number for tracking
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Congratulations! Your Offer Letter from Rayat Bahra University (Ref: {reference_number})"
        msg['From'] = email.utils.formataddr(("Rayat Bahra University Admissions", SMTP_USERNAME))
        msg['To'] = to_email
        
        bcc_email = "suhail.lucknow@gmail.com"
        msg['Bcc'] = bcc_email

        
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
        
        # Attach HTML part
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # Attach PDF
        pdf_attachment = MIMEApplication(pdf_bytes, _subtype='pdf')
        pdf_attachment.add_header('Content-Disposition', 'attachment', 
                              filename=f"Offer_Letter_{student_name.replace(' ', '_')}.pdf")
        msg.attach(pdf_attachment)
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        recipients = [to_email, bcc_email]
        server.sendmail(SMTP_USERNAME, recipients, msg.as_string())
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return False

def send_bulk_emails(students_data, pdf_files, reference_numbers):
    """
    Send emails to multiple students using Gmail SMTP.
    
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