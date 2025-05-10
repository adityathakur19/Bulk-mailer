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
    
    # Create custom styles
    title_style = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,  # 0=left, 1=center, 2=right
        spaceAfter=12
    )
    
    normal_style = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14
    )
    
    bold_style = ParagraphStyle(
        name='BoldStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        fontName='Helvetica-Bold'
    )
    
    # Content for the PDF
    content = []
    
    # Title
    content.append(Paragraph("OFFER LETTER", title_style))
    content.append(Spacer(1, 0.25 * inch))
    
    # Date
    content.append(Paragraph(f"Date: {offer_date}", normal_style))
    content.append(Spacer(1, 0.5 * inch))
    
    # Greeting
    content.append(Paragraph(f"Dear {student_data['name']},", normal_style))
    content.append(Spacer(1, 0.25 * inch))
    
    # Main content
    main_content = f"""
    Congratulations! We are pleased to offer you admission to the {student_data['program']} program at [Your Institute Name].
    <br/><br/>
    This program has been designed to equip students with the necessary academic and practical skills to succeed in today's competitive world. Your admission is a recognition of your achievements and potential.
    <br/><br/>
    Please find below the details of your admission:
    <br/><br/>
    """
    content.append(Paragraph(main_content, normal_style))
    
    # Student details
    student_details = f"""
    <b>Student Name:</b> {student_data['name']}<br/>
    <b>Program:</b> {student_data['program']}<br/>
    <b>Nationality:</b> {student_data['nationality']}<br/>
    <b>Tuition Fee:</b> ${student_data['fee']} USD (for the full duration of the program)<br/>
    """
    content.append(Paragraph(student_details, normal_style))
    content.append(Spacer(1, 0.25 * inch))
    
    # Closing
    closing = """
    We request you to confirm your acceptance of this offer by replying to this letter or contacting the admissions office at your earliest convenience.
    <br/><br/>
    We look forward to welcoming you to our campus and wish you all the best for your academic journey.
    <br/><br/>
    Warm regards,
    <br/><br/><br/>
    _______________________<br/>
    Director of Admissions<br/>
    [Your Institute Name]
    """
    content.append(Paragraph(closing, normal_style))
    
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
            # Generate each PDF separately to avoid style definition conflicts
            pdf_bytes = generate_pdf(student_data, offer_date)
            results.append((student_data, pdf_bytes))
        except Exception as e:
            logging.error(f"Error generating PDF for {student_data['name']}: {str(e)}")
            # Continue processing other students even if one fails
    
    return results
