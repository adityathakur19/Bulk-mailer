import os
import logging
import tempfile
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, jsonify, send_file, flash, session
from werkzeug.utils import secure_filename
from utils.file_processor import process_uploaded_file
from utils.pdf_generator import generate_pdf, generate_all_pdfs

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
    
    # Get selected date
    offer_date = request.form.get('date')
    if not offer_date:
        return jsonify({'error': 'Please select a date for the offer letters'}), 400
    
    try:
        # Process the uploaded file
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        # Process data
        student_data = process_uploaded_file(temp_path)
        
        # Store data in session
        session['student_data'] = student_data
        session['offer_date'] = offer_date
        
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
    
    if 'student_data' not in session or 'offer_date' not in session:
        return jsonify({'error': 'No data available. Please upload a file first.'}), 400
    
    student_data = session['student_data']
    offer_date = session['offer_date']
    
    if student_index >= len(student_data):
        return jsonify({'error': 'Invalid student index'}), 400
    
    student = student_data[student_index]
    
    try:
        # Generate PDF for a single student
        pdf_bytes = generate_pdf(student, offer_date)
        
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

@app.route('/generate-all-pdfs', methods=['POST'])
def generate_all_pdfs_route():
    if 'student_data' not in session or 'offer_date' not in session:
        return jsonify({'error': 'No data available. Please upload a file first.'}), 400
    
    student_data = session['student_data']
    offer_date = session['offer_date']
    
    try:
        # Generate all PDFs
        all_pdfs = generate_all_pdfs(student_data, offer_date)
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
