import os
import io
import logging
import math
from flask import render_template, url_for
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

def create_fee_table(student_data):
    """
    Create a table with the fee structure for the student.
    
    Args:
        student_data (dict): Dictionary containing student data
        
    Returns:
        Table: ReportLab Table object with fee structure
    """
    # Extract data for the table
    program_fee      = 3500
    one_time_fee     = student_data['one_time_fee']
    elp_fee          = student_data['tuition_fee'] 
    hostel_fee       = student_data['hostel_fee']
    first_year_total = student_data['first_year_total']
    duration_years   = int(student_data['duration'].split()[0])
    
    # Create the data for the table header with proper spacing (multi-line headers)
    data = [
        ['Year',
         'Program Fees\n(USD)/year',
         'Program Fees After\nScholarship/Year',
         'Learning Fees/Sem',
         'Hostel Fees/ Month\n(Optional)']
    ]
    
    # First year with all fees
    data.append([
        '1st Year',
        f"{program_fee}",
        "NIL",
        f"{elp_fee} USD",
        f"{hostel_fee}"
    ])
    
    # Add 2nd, 3rd, and 4th year rows (if applicable)
    year_suffixes = {2: '2nd', 3: '3rd', 4: '4th'}
    
    for year in range(2, duration_years + 1):
        year_name = year_suffixes.get(year, f"{year}th")
        data.append([
            f"{year_name} Year",   # Year label
            f"{program_fee}",      # Program Fees
            "NIL",                 # Program Fees After Scholarship
            f"{elp_fee} USD",          # Learning Fees/Sem
            f"{hostel_fee}"        # Hostel Fees Month (Optional)
        ])
    
    program_total = first_year_total + (program_fee * (duration_years - 1))

    col_widths = [80, 110, 130, 110, 100]  # Adjusted column widths for two-line headers
    
    table = Table(data, colWidths=col_widths, repeatRows=1)
    
    style = TableStyle([
    ('BACKGROUND',   (0, 0), (-1, 0), colors.lightgrey),
    ('TEXTCOLOR',    (0, 0), (-1, 0), colors.black),
    ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),  # Center all content
    ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ('TOPPADDING',   (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
    ('LEFTPADDING',  (0, 0), (-1, -1), 5),
    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ('GRID',         (0, 0), (-1, -1), 1, colors.black),
])
    
    table.setStyle(style)
    
    return table, program_total

class RBUOfferLetterTemplate(SimpleDocTemplate):
    """Custom document template with watermark and logo support"""
    
    def __init__(self, filename, **kwargs):
        SimpleDocTemplate.__init__(self, filename, **kwargs)
        self.watermark_text = "NOT VALIDFOR VISA"
    
    def build(self, flowables, onFirstPage=None, onLaterPages=None, canvasmaker=canvas.Canvas):
        """Override build method to add watermark and logos"""
        # Calculate document layout
        self._calc()
        
        # Store the canvas and template functions
        self._onFirstPage = self._watermark_and_logos
        self._onLaterPages = self._watermark_and_logos
        
        # Call the parent's build method
        SimpleDocTemplate.build(self, flowables, onFirstPage=self._onFirstPage, 
                                onLaterPages=self._onLaterPages, canvasmaker=canvasmaker)
    
    def _watermark_and_logos(self, canvas, doc):
        """Add watermark and logos to the page"""
        canvas.saveState()
        
        # Get page width and height
        width, height = doc.pagesize
        
        # Add watermark
        canvas.setFont('Helvetica', 70)
        canvas.setFillColor(colors.grey)
        canvas.setFillAlpha(0.4)  
        canvas.saveState()
        canvas.translate(width/2, height/2)  # Move to center
        canvas.rotate(45)  # Rotate 45 degrees
        canvas.drawCentredString(0, 0, self.watermark_text)
        canvas.restoreState()
        
        # Add logos
        # Left logo (RBU) - positioned at top left
        left_logo_path = os.path.join(os.getcwd(), 'static/images/rbu_logo.png')
        if os.path.exists(left_logo_path):
            # No transparency for logos - full opacity
            canvas.setFillAlpha(1.0)
            canvas.drawImage(
                left_logo_path, 
                12*mm,  # Left margin
                height - 30*mm,  # Position at top
                width=90*mm,
                height=30*mm,
                preserveAspectRatio=True,
                mask='auto'
            )
        
        # Right logo (UniPortal) - positioned at top right
        right_logo_path = os.path.join(os.getcwd(), 'static/images/uniportal_logo.png')
        if os.path.exists(right_logo_path):
            # No transparency for logos - full opacity
            canvas.setFillAlpha(1.0)
            canvas.drawImage(
                right_logo_path, 
                width - 70*mm,
                height - 20*mm,
                width=50*mm, 
                height=10*mm,
                preserveAspectRatio=True,
                mask='auto'
            )
        
        # Add a thin border line below the logo for separation
        canvas.setStrokeColor(colors.grey)
        canvas.setLineWidth(0.5)
        canvas.line(15*mm, height - 35*mm, width - 15*mm, height - 35*mm)
        
        canvas.restoreState()

def generate_pdf(student_data, offer_date, reference_number, start_date):
    """
    Generate a PDF offer letter for a student based on Rayat Bahra University template.
    
    Args:
        student_data (dict): Dictionary containing student data
        offer_date (str): Date for the offer letter
        reference_number (str): Reference number for the offer letter
        start_date (str): Tentative start date
        
    Returns:
        bytes: PDF content as bytes
    """
    buffer = io.BytesIO()
    
    # Create the PDF document with custom template - adjusted margins for better layout
    doc = RBUOfferLetterTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=40*mm,
        bottomMargin=20*mm
    )
    
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    ref_style = ParagraphStyle(
        name='RefStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        fontName='Helvetica-Bold'
    )
    
    title_style = ParagraphStyle(
    name='TitleStyle',
    parent=styles['Heading1'],
    fontSize=12,
    alignment=1,  # 0=left, 1=center, 2=right
    spaceAfter=5 * mm,
    fontName='Helvetica-Bold'
)
    
    student_info_style = ParagraphStyle(
        name='StudentInfoStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14
    )
    
    normal_style = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    
    bold_style = ParagraphStyle(
        name='BoldStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        name='HeaderStyle',
        parent=styles['Heading2'],
        fontSize=12,
        fontName='Helvetica-Bold'
    )
    
    # Content for the PDF
    content = []
    
    # Reference number
    content.append(Paragraph(reference_number, ref_style))
    content.append(Spacer(1, 5*mm))
    
    # Title
    content.append(Paragraph("<u>OFFER LETTER</u>", title_style))
    content.append(Spacer(1, 5*mm))
    
    # Student info and date table with improved layout
    student_info = [
        [Paragraph(f"<b>Student Name:</b> {student_data['name'].upper()}", student_info_style), 
         Paragraph(f"<b>Date of offer:</b> {offer_date}", student_info_style)],
        [Paragraph(f"<b>Nationality:</b> {student_data['nationality'].upper()}", student_info_style), 
         Paragraph("", student_info_style)]
    ]
    
    # Better width distribution for student info
    student_table = Table(student_info, colWidths=[doc.width * 0.6, doc.width * 0.4])
    student_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
    ]))
    
    content.append(student_table)
    content.append(Spacer(1, 5*mm))
    
    # Greeting
    content.append(Paragraph("Dear Applicant,", normal_style))
    content.append(Spacer(1, 3*mm))
    
    # Main content
    main_content = """
    We are pleased to confirm that our Academic Board has reviewed your application along with your certificate and 
    we found you eligible for the academic program as mentioned below, at Rayat Bahra University for the upcoming session. 
    On this basis, we are issuing this offer letter for your acceptance and confirmation with payment of registration fee 
    as specified in the document within 03 days of date of issue of this offer letter:
    """
    content.append(Paragraph(main_content, normal_style))
    content.append(Spacer(1, 5*mm))
    
    # Program details table with improved columns
    program_details = [
        ["Program Name", student_data['program'].upper()],
        ["Program Duration", student_data['duration']],
        ["Tentative Start Date", start_date],
        ["Name of the University", "RAYAT BAHRA UNIVERSITY"],
        ["University Address", "V.P.O. Sahauran, Tehsil Kharar, Distt. Mohali, Kharar, Punjab 140301"],
        ["Scholarship Awarded", student_data['scholarship']]
    ]
    
    # Better width distribution (30% - 70%)
    program_table = Table(program_details, colWidths=[doc.width * 0.3, doc.width * 0.7])
    program_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6)
    ]))
    
    content.append(program_table)
    content.append(Spacer(1, 5*mm))
    
    # Fee structure header
    content.append(Paragraph("Fee Structure after scholarship:", bold_style))
    content.append(Spacer(1, 3*mm))
    
    # Fee structure table - using the improved function
    fee_table, program_total = create_fee_table(student_data)
    content.append(fee_table)
    content.append(Spacer(1, 2*mm))
    
    # Fee notes
    fee_notes = """
    *one time Admissions – 500 USD: Hostel with Mess service @1500 USD per year. One time fees is not part of the tuition & hostel fees. FRO CHARGES ONE TIME – 50 USD; Exam Fees Per Sem = 50 USD; HEALTH INSURANCE–150 USD/YEAR

    """
    content.append(Paragraph(fee_notes, normal_style))
    content.append(Spacer(1, 5*mm))
    
    # Provisional admission note
    provisional_note = """
    This admission letter is provisional and subject to production of final result and proof of payment of fees. 
    Failing which the admission shall be cancelled and no refund shall be entertained.
    """
    content.append(Paragraph(provisional_note, normal_style))
    
    # Add page break to ensure conditions start on a new page
    content.append(PageBreak())
    
    # Conditions header
    content.append(Paragraph("CONDITIONS TO ACCEPT THIS ADMISSION OFFER LETTER", header_style))
    content.append(Spacer(1, 3*mm))
    
    # Conditions list
    conditions = [
        "The admission shall be confirmed after verification of all the necessary documents as mentioned below.",
        "Payment Proof of full first year fees transferred to the University's account.",
        "Copy of Passport & Passport size photograph.",
        "Academic Transcripts (if not in English Language, please submit the translated copy in English).",
        "The offered admission stands cancelled if the registration fee is not paid within 03 days of receipt of this Offer Letter.",
        "On-campus accommodation is mandatory for the first year and FRRO assistance will not be provided to students staying outside the University Campus.",
        "Accommodation fee shall be charged on annual basis and facility once activated will not be cancelled or refunded."
    ]
    
    for condition in conditions:
        bullet_text = f"• {condition}"
        content.append(Paragraph(bullet_text, normal_style))
        content.append(Spacer(1, 2*mm))
    
    content.append(Paragraph("Please send the scanned copy of all above-mentioned documents at do@bahrauniversity.edu.in to receive the Acceptance letter.", normal_style))
    
    # Add a page break
    content.append(Spacer(1, 20*mm))
    
    # Payment details header
    content.append(Paragraph("PAYMENT TRANSFER DETAILS", header_style))
    content.append(Spacer(1, 3*mm))
    
    # Payment notes
    payment_notes = [
        "Please mention the student's name at the time of SWIFT transfer of school fee from your bank.",
        "All International transactions should be made in US Dollars only.",
        "Issuance of Fee Receipt is subject to realization of the fee transferred in the bank account.",
        "Please use the following Bank Account details to transfer the School Fee."
    ]
    
    for note in payment_notes:
        bullet_text = f"• {note}"
        content.append(Paragraph(bullet_text, normal_style))
        content.append(Spacer(1, 2*mm))
    
    content.append(Spacer(1, 3*mm))
    
    # Bank details table with better width distribution and handling long address
    bank_details = [
        ["BANK NAME", "PUNJAB NATIONAL BANK"],
        ["BANK ADDRESS", "VILL- SAHAURAN, RAYAT BAHRA INSTITUTE,\nDISST-SAS NAGAR, PUNJAB- 140104"],
        ["ACCOUNT NAME", "INTERNATIONAL ADMISSION RAYAT BAHRA GROUP OF INSTITUTES"],
        ["ACCOUNT NUMBER", "19341132000031"],
        ["SWIFT CODE", "PUNBINBBISB"],
        ["IFSC / MICR CODE", "PUNB0193410 / 160024145"]
    ]
    
    # Better width distribution (28% - 72%) with adequate space for content
    bank_table = Table(bank_details, colWidths=[doc.width * 0.28, doc.width * 0.72])
    bank_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('WORDWRAP', (0, 0), (-1, -1), True)  # Enable word wrapping for all cells
    ]))
    
    content.append(bank_table)
    content.append(Spacer(1, 10*mm))
    
    # Important instructions header
    content.append(Paragraph("IMPORTANT INSTRUCTIONS FOR THE STUDENTS:", header_style))
    content.append(Spacer(1, 3*mm))
    
    
    
    # Instructions list
    instructions = [
        "You have applied for a full-time program studying at Rayat Bahra University.",
        "It is our policy to monitor and track progression of students throughout their studies in accordance with the norms of Rayat Bahra University.",
        "Consumption of alcohol/all types of intoxicants is strictly banned in the campus and hostels.",
        "You shall be governed by the rules and regulations of Rayat Bahra University.",
        "You are required to pay the complete fee for the first year before reporting to the campus. Students studying for programs that are longer than one year in duration, will be required to pay advance fee before the commencement of each subsequent year of study.",
        "All charges levied by bank on bank transfers are to be borne by the student. In case the amount transferred by the student is received short of the required fee, the student to clear all the dues will deposit the same deficit.",
        "Your admission will be confirmed on verification of original certificates of qualifying examination, failing which will lead to cancellation of admission and you will not be eligible for any refund in such case.",
        "The university reserves the rights to discontinue/Cancel/change the program offered at any point of time."
    ]

    for instruction in instructions:
        bullet_text = f"• {instruction}"
        content.append(Paragraph(bullet_text, normal_style))
        content.append(Spacer(1, 2*mm))
    
    content.append(Spacer(1, 2*mm))
    content.append(Paragraph("Please sign this Document and send us the scanned copy as a proof of acceptance on do@bahrauniversity.edu.in. or Whatsapp on +9184769-12345", normal_style))
    content.append(Spacer(1, 5*mm))

    # Add signature image before building the PDF
    signature_path = os.path.join(os.getcwd(), 'static/images/sign.png')
    if os.path.exists(signature_path):
        signature_img = Image(signature_path, width=60*mm, height=40*mm)
    signature_img.hAlign = 'LEFT'   
    content.append(signature_img)
    
    # Build the PDF document
    doc.build(content)
    
    # Get the PDF content
    pdf_data = buffer.getvalue()
    buffer.close()
    
    return pdf_data


def generate_all_pdfs(student_data_list, offer_date, ref_number_start, start_date):
    """
    Generate PDFs for all students.
    
    Args:
        student_data_list (list): List of dictionaries containing student data
        offer_date (str): Date for the offer letters
        ref_number_start (int): Starting reference number
        start_date (str): Tentative start date
        
    Returns:
        list: List of tuples containing (student_data, pdf_bytes)
    """
    results = []
    
    for index, student_data in enumerate(student_data_list):
        try:
            # Generate reference number for this student
            reference_number = f"RBU/DIA25/OL-{ref_number_start + index:04d}"
            
            # Generate PDF for this student
            pdf_bytes = generate_pdf(student_data, offer_date, reference_number, start_date)
            results.append((student_data, pdf_bytes))
            
            # Log success
            logging.info(f"Successfully generated PDF for {student_data['name']} with reference {reference_number}")
            
        except Exception as e:
            logging.error(f"Error generating PDF for {student_data['name']}: {str(e)}")
            # Continue processing other students even if one fails
    
    
    return results
