import os
import logging
import tempfile
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, flash, session
from werkzeug.utils import secure_filename
from utils.file_processor import process_uploaded_file
from utils.pdf_generator import generate_pdf, generate_all_pdfs
from utils.gmail_sender import send_offer_letter_email, send_bulk_emails

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure file upload settings
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file is present in the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # Check if file is selected
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Get form data
    offer_date = request.form.get('date')
    if not offer_date:
        return jsonify({'error': 'Please select a date for the offer letters'}), 400
    
    # Get reference number starting point
    ref_number_start = request.form.get('ref_number')
    if not ref_number_start:
        return jsonify({'error': 'Please enter a starting reference number'}), 400
    
    try:
        ref_number_start = int(ref_number_start)
    except ValueError:
        return jsonify({'error': 'Reference number must be a 4-digit number'}), 400
        
    if ref_number_start < 1000 or ref_number_start > 9999:
        return jsonify({'error': 'Reference number must be a 4-digit number'}), 400
    
    # Get tentative start date
    start_date = request.form.get('start_date')
    if not start_date:
        return jsonify({'error': 'Please select a tentative start date'}), 400
    
    try:
        # Process the uploaded file
        if file.filename is None:
            return jsonify({'error': 'Invalid filename'}), 400
            
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        # Process data
        student_data = process_uploaded_file(temp_path)
        
        # Store data in session
        session['student_data'] = student_data
        session['offer_date'] = offer_date
        session['ref_number_start'] = ref_number_start
        session['start_date'] = start_date
        
        # Clean up
        os.remove(temp_path)
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(student_data)} student records',
            'preview': student_data[:5]  # Send first 5 records for preview
        })
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf_route():
    # Get individual student data
    student_index = int(request.form.get('index', 0))
    
    if 'student_data' not in session or 'offer_date' not in session or 'ref_number_start' not in session or 'start_date' not in session:
        return jsonify({'error': 'No data available. Please upload a file first.'}), 400
    
    student_data = session['student_data']
    offer_date = session['offer_date']
    ref_number_start = session['ref_number_start']
    start_date = session['start_date']
    
    if student_index >= len(student_data):
        return jsonify({'error': 'Invalid student index'}), 400
    
    student = student_data[student_index]
    
    # Generate reference number (increment by student index)
    reference_number = f"RBU/DIA25/OL-{ref_number_start + student_index:04d}"
    
    try:
        # Generate PDF for a single student
        pdf_bytes = generate_pdf(student, offer_date, reference_number, start_date)
        
        # Send the PDF file
        mem_file = BytesIO(pdf_bytes)
        mem_file.seek(0)
        
        filename = f"offer_letter_{student['name'].replace(' ', '_')}.pdf"
        
        return send_file(
            mem_file,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        return jsonify({'error': f'Error generating PDF: {str(e)}'}), 500

@app.route('/send-email', methods=['POST'])
def send_email_route():
    # Get individual student data
    student_index = int(request.form.get('index', 0))
    
    if 'student_data' not in session or 'offer_date' not in session or 'ref_number_start' not in session or 'start_date' not in session:
        return jsonify({'error': 'No data available. Please upload a file first.'}), 400
    
    student_data = session['student_data']
    offer_date = session['offer_date']
    ref_number_start = session['ref_number_start']
    start_date = session['start_date']
    
    if student_index >= len(student_data):
        return jsonify({'error': 'Invalid student index'}), 400
    
    student = student_data[student_index]
    
    # Check if email is available
    if not student.get('email'):
        return jsonify({'error': 'No email address available for this student'}), 400
    
    # Generate reference number (increment by student index)
    reference_number = f"RBU/DIA25/OL-{ref_number_start + student_index:04d}"
    
    try:
        # Generate PDF for a single student
        pdf_bytes = generate_pdf(student, offer_date, reference_number, start_date)
        
        # Send email with PDF attachment
        email_sent = send_offer_letter_email(
            student['email'],
            student['name'],
            pdf_bytes,
            reference_number
        )
        
        if email_sent:
            return jsonify({
                'success': True,
                'message': f"Offer letter successfully sent to {student['email']}"
            })
        else:
            return jsonify({
                'error': 'Failed to send email. Please check your email settings.'
            }), 500
    
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return jsonify({'error': f'Error sending email: {str(e)}'}), 500

@app.route('/generate-all-pdfs', methods=['POST'])
def generate_all_pdfs_route():
    if 'student_data' not in session or 'offer_date' not in session or 'ref_number_start' not in session or 'start_date' not in session:
        return jsonify({'error': 'No data available. Please upload a file first.'}), 400
    
    student_data = session['student_data']
    offer_date = session['offer_date']
    ref_number_start = session['ref_number_start']
    start_date = session['start_date']
    
    try:
        # Generate all PDFs
        all_pdfs = generate_all_pdfs(student_data, offer_date, ref_number_start, start_date)
        
        # Create a ZIP file
        mem_zip = BytesIO()
        with zipfile.ZipFile(mem_zip, 'w') as zf:
            for student, pdf_bytes in all_pdfs:
                filename = f"offer_letter_{student['name'].replace(' ', '_')}.pdf"
                zf.writestr(filename, pdf_bytes)
        
        mem_zip.seek(0)
        
        return send_file(
            mem_zip,
            mimetype='application/zip',
            as_attachment=True,
            download_name='offer_letters.zip'
        )
    
    except Exception as e:
        logging.error(f"Error generating PDFs: {str(e)}")
        return jsonify({'error': f'Error generating PDFs: {str(e)}'}), 500

@app.route('/send-all-emails', methods=['POST'])
def send_all_emails_route():
    if 'student_data' not in session or 'offer_date' not in session or 'ref_number_start' not in session or 'start_date' not in session:
        return jsonify({'error': 'No data available. Please upload a file first.'}), 400
    
    student_data = session['student_data']
    offer_date = session['offer_date']
    ref_number_start = session['ref_number_start']
    start_date = session['start_date']
    
    # Check if all students have email addresses
    missing_emails = [student['name'] for student in student_data if not student.get('email')]
    if missing_emails:
        return jsonify({
            'error': f"The following students are missing email addresses: {', '.join(missing_emails)}"
        }), 400
    
    try:
        # Generate all PDFs
        all_pdfs = generate_all_pdfs(student_data, offer_date, ref_number_start, start_date)
        
        # Create reference numbers
        reference_numbers = [
            f"RBU/DIA25/OL-{ref_number_start + i:04d}" for i in range(len(student_data))
        ]
        
        # Extract PDF bytes from the tuple list
        pdf_files = [pdf_bytes for _, pdf_bytes in all_pdfs]
        
        # Send emails to all students
        results = send_bulk_emails(student_data, pdf_files, reference_numbers)
        
        return jsonify({
            'success': True,
            'message': f"Completed: {results['success']} emails sent, {results['failed']} failed",
            'details': results['details']
        })
    
    except Exception as e:
        logging.error(f"Error sending emails: {str(e)}")
        return jsonify({'error': f'Error sending emails: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
