import os
import logging
import tempfile
import zipfile
from io import BytesIO
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file, flash
from werkzeug.utils import secure_filename
from utils.file_processor import process_uploaded_file
from utils.pdf_generator import generate_pdf, generate_all_pdfs
from utils.gmail_sender import send_offer_letter_email, send_bulk_emails
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "temp_secret_key_for_development")

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["RBU"]
collection = db["offer_letter_data"]

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
        # save & process
        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        # 1) process into a list of dicts
        student_data = process_uploaded_file(temp_path)
        
        # 2) clean NaN → None so jsonify emits valid JSON null
        df = pd.DataFrame(student_data)
        df = df.where(pd.notnull(df), None)
        student_data = df.to_dict(orient='records')
        
        # 3) Store in MongoDB instead of session
        data_document = {
            'student_data': student_data,
            'offer_date': offer_date,
            'ref_number_start': ref_number_start,
            'start_date': start_date,
            'created_at': pd.Timestamp.now().isoformat()
        }
        
        # Insert into MongoDB and get the generated ID
        result = collection.insert_one(data_document)
        data_id = str(result.inserted_id)
        
        # cleanup temp file
        os.remove(temp_path)
        
        # 4) return ALL records with MongoDB ID
        return jsonify({
            'success': True,
            'message': f'Successfully processed {len(student_data)} student records',
            'preview': student_data,
            'data_id': data_id  # Return MongoDB document ID for future reference
        })
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf_route():
    # Get individual student data
    student_index = int(request.form.get('index', 0))
    data_id = request.form.get('data_id')
    
    if not data_id:
        return jsonify({'error': 'No data ID provided. Please upload a file first.'}), 400
    
    try:
        # Get data from MongoDB using the ID
        data_document = collection.find_one({'_id': ObjectId(data_id)})
        
        if not data_document:
            return jsonify({'error': 'Data not found in database. Please upload a file again.'}), 404
        
        student_data = data_document.get('student_data', [])
        offer_date = data_document.get('offer_date')
        ref_number_start = data_document.get('ref_number_start')
        start_date = data_document.get('start_date')
        
        # Validate required fields
        if not all([student_data, offer_date, ref_number_start, start_date]):
            missing = []
            for field, value in [('student_data', student_data), ('offer_date', offer_date), 
                                ('ref_number_start', ref_number_start), ('start_date', start_date)]:
                if not value:
                    missing.append(field)
            return jsonify({'error': f'Missing required data: {", ".join(missing)}'}), 400
        
        if student_index >= len(student_data):
            return jsonify({'error': 'Invalid student index'}), 400
        
        student = student_data[student_index]
        
        # Generate reference number (increment by student index)
        reference_number = f"RBU/DIA25/OL-{ref_number_start + student_index:04d}"
        
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

@app.route('/data-status', methods=['GET'])
def data_status():
    """Check data status in MongoDB"""
    data_id = request.args.get('data_id')
    
    if not data_id:
        return jsonify({'error': 'No data ID provided'}), 400
    
    try:
        data_document = collection.find_one({'_id': ObjectId(data_id)})
        
        if not data_document:
            return jsonify({'exists': False})
        
        num_students = len(data_document.get('student_data', []))
        
        return jsonify({
            'exists': True,
            'num_students': num_students,
            'offer_date': data_document.get('offer_date'),
            'ref_number_start': data_document.get('ref_number_start'),
            'start_date': data_document.get('start_date')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate-all-pdfs', methods=['POST'])
def generate_all_pdfs_route():
    data_id = request.form.get('data_id')
    
    if not data_id:
        return jsonify({'error': 'No data ID provided. Please upload a file first.'}), 400
    
    try:
        # Get data from MongoDB
        data_document = collection.find_one({'_id': ObjectId(data_id)})
        
        if not data_document:
            return jsonify({'error': 'Data not found in database. Please upload a file again.'}), 404
        
        student_data = data_document.get('student_data', [])
        offer_date = data_document.get('offer_date')
        ref_number_start = data_document.get('ref_number_start')
        start_date = data_document.get('start_date')
        
        # Validate the data
        if not student_data or not isinstance(student_data, list):
            logging.error(f"Invalid student_data format: {type(student_data)}")
            return jsonify({'error': 'Invalid student data format. Please upload file again.'}), 400
        
        logging.info(f"Found {len(student_data)} students in database")
        
        # Create a temporary directory to store PDFs
        temp_dir = tempfile.mkdtemp()
        zip_filepath = os.path.join(temp_dir, 'offer_letters.zip')
        
        # Log info for debugging
        logging.info(f"Processing {len(student_data)} student records into {zip_filepath}")
        
        # Process in batches to avoid memory issues
        batch_size = 50
        total_batches = (len(student_data) + batch_size - 1) // batch_size
        
        # Create the ZIP file on disk instead of in memory
        with zipfile.ZipFile(zip_filepath, 'w') as zf:
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(student_data))
                
                logging.info(f"Processing batch {batch_num+1}/{total_batches} (students {start_idx}-{end_idx-1})")
                
                # Process each student in the current batch
                for i in range(start_idx, end_idx):
                    student = student_data[i]
                    
                    try:
                        # Generate reference number
                        reference_number = f"RBU/DIA25/OL-{ref_number_start + i:04d}"
                        
                        # Create safe versions of all fields
                        safe_student = {}
                        for key, value in student.items():
                            safe_student[key] = "" if value is None else value
                        
                        # Generate PDF for this student
                        pdf_bytes = generate_pdf(safe_student, offer_date, reference_number, start_date)
                        
                        if pdf_bytes:
                            # Use a safe student name (fallback to index if name is missing)
                            student_name = safe_student.get('name', f"student_{i}")
                            if not student_name:
                                student_name = f"student_{i}"
                            
                            # Create filename for this PDF
                            filename = f"offer_letter_{student_name.replace(' ', '_')}.pdf"
                            
                            # Add to ZIP
                            zf.writestr(filename, pdf_bytes)
                            
                    except Exception as e:
                        # Log the error but continue with other students
                        logging.error(f"Error processing student {i}: {str(e)}")
                        continue
        
        # Send the file from disk
        return send_file(
            zip_filepath,
            mimetype='application/zip',
            as_attachment=True,
            download_name='offer_letters.zip',
            # Important: This will automatically remove the temp files after sending
            max_age=0
        )
    
    except Exception as e:
        logging.error(f"Error generating PDFs: {str(e)}")
        return jsonify({'error': f'Error generating PDFs: {str(e)}'}), 500

@app.route('/send-email', methods=['POST'])
def send_email_route():
    # Get individual student data
    student_index = int(request.form.get('index', 0))
    data_id = request.form.get('data_id')
    
    if not data_id:
        return jsonify({'error': 'No data ID provided. Please upload a file first.'}), 400
    
    try:
        # Get data from MongoDB
        data_document = collection.find_one({'_id': ObjectId(data_id)})
        
        if not data_document:
            return jsonify({'error': 'Data not found in database. Please upload a file again.'}), 404
        
        student_data = data_document.get('student_data', [])
        offer_date = data_document.get('offer_date')
        ref_number_start = data_document.get('ref_number_start')
        start_date = data_document.get('start_date')
        
        if student_index >= len(student_data):
            return jsonify({'error': 'Invalid student index'}), 400
        
        student = student_data[student_index]
        
        # Check if email is available
        if not student.get('email'):
            return jsonify({'error': 'No email address available for this student'}), 400
        
        # Generate reference number (increment by student index)
        reference_number = f"RBU/DIA25/OL-{ref_number_start + student_index:04d}"
        
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

@app.route('/send-all-emails', methods=['POST'])
def send_all_emails_route():
    data_id = request.form.get('data_id')
    
    if not data_id:
        return jsonify({'error': 'No data ID provided. Please upload a file first.'}), 400
    
    try:
        # Get data from MongoDB
        data_document = collection.find_one({'_id': ObjectId(data_id)})
        
        if not data_document:
            return jsonify({'error': 'Data not found in database. Please upload a file again.'}), 404
        
        student_data = data_document.get('student_data', [])
        offer_date = data_document.get('offer_date')
        ref_number_start = data_document.get('ref_number_start')
        start_date = data_document.get('start_date')
        
        # Check if all students have email addresses
        missing_emails = [student['name'] for student in student_data if not student.get('email')]
        if missing_emails:
            return jsonify({
                'error': f"The following students are missing email addresses: {', '.join(missing_emails)}"
            }), 400
        
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

@app.route('/list-uploads', methods=['GET'])
def list_uploads():
    """List all uploaded data sets in the MongoDB collection"""
    try:
        # Find all documents, sort by creation time (newest first)
        documents = collection.find({}, {'student_data': 0}).sort('created_at', -1)
        
        # Convert documents to a list of dicts
        results = []
        for doc in documents:
            doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
            # Get student count from the document
            student_count = len(collection.find_one({'_id': ObjectId(doc['_id'])}, 
                                                  {'student_data': 1, '_id': 0})
                              .get('student_data', []))
            doc['student_count'] = student_count
            results.append(doc)
        
        return jsonify({
            'success': True,
            'uploads': results
        })
    except Exception as e:
        logging.error(f"Error listing uploads: {str(e)}")
        return jsonify({'error': f'Error listing uploads: {str(e)}'}), 500

@app.route('/delete-upload', methods=['POST'])
def delete_upload():
    """Delete an uploaded data set"""
    data_id = request.form.get('data_id')
    
    if not data_id:
        return jsonify({'error': 'No data ID provided'}), 400
    
    try:
        # Delete the document
        result = collection.delete_one({'_id': ObjectId(data_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Data not found in database'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Data deleted successfully'
        })
    except Exception as e:
        logging.error(f"Error deleting upload: {str(e)}")
        return jsonify({'error': f'Error deleting upload: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)