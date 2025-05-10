import os
import io
import logging
from flask import render_template
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_pdf(student_data, offer_date):
    """
    Generate a PDF offer letter for a student.
    
    Args:
        student_data (dict): Dictionary containing student data
        offer_date (str): Date for the offer letter
        
    Returns:
        bytes: PDF content as bytes
    """
    buffer = io.BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Create a custom style for the heading
    styles.add(ParagraphStyle(
        name='Heading1',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # 0=left, 1=center, 2=right
        spaceAfter=12
    ))
    
    # Content for the PDF
    content = []
    
    # University Name
    university_name = "GLOBAL UNIVERSITY"
    content.append(Paragraph(university_name, styles['Heading1']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Date
    content.append(Paragraph(f"Date: {offer_date}", styles['Normal']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Student Name
    content.append(Paragraph(f"To: {student_data['name']}", styles['Normal']))
    content.append(Paragraph(f"Nationality: {student_data['nationality']}", styles['Normal']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Subject
    content.append(Paragraph("SUBJECT: OFFER LETTER", styles['Heading2']))
    content.append(Spacer(1, 0.25 * inch))
    
    # Letter content
    letter_content = f"""
    Dear {student_data['name']},<br/><br/>
    
    We are pleased to offer you admission to our {student_data['program']} program at Global University.
    Based on your academic records and qualifications, we believe you will be a valuable addition to our institution.<br/><br/>
    
    <b>Program Details:</b><br/>
    Program: {student_data['program']}<br/>
    Tuition Fee: ${student_data['fee']}<br/><br/>
    
    We look forward to your acceptance of this offer and to welcoming you to Global University.
    Please let us know your decision by responding to this letter within 30 days of the offer date.<br/><br/>
    
    Sincerely,<br/><br/>
    
    Prof. Jane Smith<br/>
    Dean of Admissions<br/>
    Global University
    """
    
    content.append(Paragraph(letter_content, styles['Normal']))
    
    # Build the PDF document
    doc.build(content)
    
    # Get the PDF content
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data

def generate_all_pdfs(student_data_list, offer_date):
    """
    Generate PDFs for all students.
    
    Args:
        student_data_list (list): List of dictionaries containing student data
        offer_date (str): Date for the offer letters
        
    Returns:
        list: List of tuples containing (student_data, pdf_bytes)
    """
    results = []
    
    for student_data in student_data_list:
        try:
            pdf_bytes = generate_pdf(student_data, offer_date)
            results.append((student_data, pdf_bytes))
        except Exception as e:
            logging.error(f"Error generating PDF for {student_data['name']}: {str(e)}")
    
    return results
