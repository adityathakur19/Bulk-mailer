import pandas as pd
import os
import logging

def determine_program_details(program_name):
    """
    Determine program details including fee, duration, and hostel fees.
    
    Args:
        program_name (str): The name of the program
        
    Returns:
        dict: Dictionary with program details (fee, duration, hostel_fee)
    """
    program_name = program_name.lower()
    result = {
        'tuition_fee': 0,
        'duration': '',
        'hostel_fee': 150,  # Default hostel fee
        'one_time_fee': 500,  # Default one-time fee
        'program_type': ''
    }
    
    # Define program categories with comprehensive lists
    engineering_programs = [
        'b.tech', 'btech', 'bachelor of technology', 'bachelor of engineering',
        'b.e', 'be', 'beng', 'mechanical engineering', 'civil engineering',
        'electrical engineering', 'computer engineering', 'computer science',
        'electrical and electronics engineering', 'automobile engg', 'mechtronics',
        'aerospace engineering', 'biomedical engineering', 'electronics & computer science engineering',
        'electronics & communication engineering', 'chemical engineering', 'cse'
    ]
    
    # Bachelor's degree programs (3-year)
    bachelor_3yr_keywords = [
        'bsc', 'b.sc', 'bachelor of science', 'bsc it', 'b.sc. (it)', 
        'bca', 'bca - specialization in artificial intelligence (ai)', 
        'bca nextgen - specialization in data science', 'bca (internet of things)',
        'bca (data science)', 'bca (artificial intelligence)',
        'b.sc. in airport & cargo management', 'b.sc. in home science & hospitality management',
        'b.sc. in airlines & airport management', 'bsc biotechnology',
        'bsc multimédia', 'bsc mathematics', 'bsc agriculture', 'bsc environment science',
        'BSc IT',
        'bba', 'bachelor of business administration', 'bba digital marketing',
        'bba hrm', 'bba logistics', 'bba logistisc and transport', 'bba international',
        'business administration', 'bba finance & accounts', 'bba in logistics',
        
        'b.com', 'bachelor of commerce', 'b.com (hons.)', 'bcom',
        'b.com (banking and finance)', 'b.com (finanace & accounts)',
        'accounting and financial management',
        
        'llb', 'ba-llb','ll.b', 'bachelor of law', 'bachelor of arts and law','b of law',
        
        'ba', 'bachelor of arts', 'ba psychology', 'ba economics', 'ba english',
        'ba social work', 'ba economic', 'ba social science', 'ba strategic studies',
        'ba arts', 'ba filmmaking & tv production',
        'b.a. (punjabi, hindi, english, sociology, psychology, political science, history)',
        'b.a. ( english language and literature )',
        'ba arts',
        
        'bachelor in hotel mgmt.', 'b. vocational in personal care and wellness',
        'b.vocational in fashion designing', 'b.vocational in interior designing',
        'b.a. in fine arts', 'b.a hons (economics, public administration, computer)',
        'b.p.e.s.', 'b.sc life sciences (medical)', 'b.sc physical sciences (non-medical)',
        'b.sc in food science and technology', 'bsc forensic science',
        'bsc cardiovascular technology', 'b.sc fashion designing',
        'ba in mass communication and journalism', 'b.sc fashion management',
        'bpt'
    ]
    
    # Medical programs (4-year)
    medical_4yr_keywords = [
        'bsc operations theatre', 'bsc radiology', 'bsc medical', 'bsc clinical medicine',
        'bsc optometry', 'b.sc nutrition', 'b.sc. medical laboratory science',
        'master in medicine', 'bsc. medicine', 'b.sc. medicine',
        'b.sc medical microbiology', 'b.sc medical laboratory sciences',
        'bsc medical radiology & imaging technology', 'b.sc clinical embryology',
        'b.sc stem cell technologies & regenerative medicines',
        'b.sc nutrigenetics and personalised nutrition',
        'b.sc nursing',
        'bsc nursing'
    ]
    
    pharmacy_bachelor_keywords = [
        'b.pharma', 'b pharma', 'bachelor of pharmacy', 'b pharmacy', 'b.pharmacy', 'pharmacy'
    ]
    
    pharmacy_master_keywords = [
        'm.pharma', 'm pharma', 'master of pharmacy', 'm pharmacy'
    ]
    
    # All Bachelor's degree keywords (general)
    all_bachelor_keywords = engineering_programs + bachelor_3yr_keywords + pharmacy_bachelor_keywords + medical_4yr_keywords + ['bachelor', 'undergraduate']
    
    # Master's degree keywords
    master_keywords = [
        'master', 'msc', 'ma', 'meng', 'mba', 'MBA', 'm.tech', 'mca',
        'm.sc', 'm.a', 'm.com', 'mcom', 'ms', 'post graduate', 'pg',
        'master in public health', 'masters in public health', 'hospitals administration',
        'mba marketing',
        'm.tech computer science & engineering', 
        'm.tech mechanical engineering',
        'm.tech computer science & engineering',
        'm.tech production engineering', 'm.tech electrical engineering',
        'm.tech civil engineering', 'm.tech electronics and communication engineering',
        'm.tech environmental engineering', 'm.tech (part time) computer science & engineering',
        'm.tech (part time) mechanical engineering', 'm.tech (part time) electronics & communication engineering'
    ]
    
    # PhD keywords
    phd_keywords = [
        'ph.d. engineering & technology', 'doctorate', 'doctoral', 'ph.d', 'doctor of philosophy'
    ]
    
    # Diploma keywords
    diploma_keywords = [
        'diploma', 'certificate', 'pgd', 'post graduate diploma',
        'diploma in computer science & engineering', 'diploma in mechanical engineering',
        'diploma in electronics & communication engineering', 'diploma in automobile engineering',
        'diploma in electrical engineering', 'diploma in civil engineering',
        'diploma computer science engineering'
    ]
    
    # Specialized overrides (checked early!)
    ai_ml_keywords = [
        'btech_aiml', 'ai_ml', 'btech_ai_ml','btech ai ml', 'btech artificial intelligence',
        'btech machine learning', 'b.tech ai', 'b.tech ml', 'aiml', 'cyber security',
        'b.tech aiml', 'b.tech aiml / cyber security'
    ]
    
    if any(kw in program_name for kw in ai_ml_keywords):
        result.update({
            'tuition_fee': 1000,
            'duration': '04 YEARS',
            'program_type': 'Bachelor'
        })
    elif any(kw in program_name for kw in diploma_keywords):
        result.update({
            'tuition_fee': 700,
            'duration': '03 YEAR',
            'program_type': 'Diploma'
        })
    elif 'mba' in program_name:
        result.update({
            'tuition_fee': 800, 
            'duration': '02 YEARS',
            'program_type': 'Master'
        })
    # Pharmacy programs
    elif any(kw in program_name for kw in pharmacy_bachelor_keywords):
        result.update({
            'tuition_fee': 1000,
            'duration': '04 YEARS',
            'program_type': 'Bachelor'
        })
    elif any(kw in program_name for kw in pharmacy_master_keywords):
        result.update({
            'tuition_fee': 1000,
            'duration': '02 YEARS',
            'program_type': 'Master'
        })
    # Medical programs (4-year bachelor's)
    elif any(kw in program_name for kw in medical_4yr_keywords):
        result.update({
            'tuition_fee': 750,
            'duration': '04 YEARS',
            'program_type': 'Bachelor'
        })
    # Engineering or BCA programs (4-year bachelors)
    elif any(kw in program_name for kw in engineering_programs) or 'bca' in program_name:
        result.update({
            'tuition_fee': 750,
            'duration': '04 YEARS',
            'program_type': 'Bachelor'
        })
    # 3-year bachelor programs
    elif any(kw in program_name for kw in bachelor_3yr_keywords):
        result.update({
            'tuition_fee': 750,
            'duration': '03 YEARS',
            'program_type': 'Bachelor'
        })
    # Generic bachelor's degrees
    elif any(kw in program_name for kw in all_bachelor_keywords):
        result.update({
            'tuition_fee': 750,
            'duration': '03 YEARS',
            'program_type': 'Bachelor'
        })
    # Master's programs
    elif 'mca' in program_name or any(kw in program_name for kw in master_keywords):
        result.update({
            'tuition_fee': 800,
            'duration': '02 YEARS',
            'program_type': 'Master'
        })
    # PhD programs
    elif any(kw in program_name for kw in phd_keywords):
        result.update({
            'tuition_fee': 1500,
            'duration': '03 YEARS',
            'program_type': 'PhD'
        })
    # Default to bachelor's if nothing else matches
    else:
        result.update({
            'tuition_fee': 1600,
            'duration': '03 YEARS',
            'program_type': 'Bachelor'
        })
    
    # Foundation year bump
    if 'foundation' in program_name or 'pathway' in program_name:
        if result['program_type'] == 'Bachelor' and result['duration'] == '03 YEARS':
            result['duration'] = '04 YEARS'
    
    # Scholarship & ELP
    result['scholarship'] = "CHANCELLOR'S Scholarship"
    result['elp_fee'] = 500 if ('foundation' in program_name or 'english' in program_name) else 0
    
    return result

def determine_fee(program_name):
    """
    Determine the fee based on the program type (for backward compatibility).
    
    Args:
        program_name (str): The name of the program
        
    Returns:
        int: The fee amount
    """
    return determine_program_details(program_name)['tuition_fee']

def process_uploaded_file(file_path):
    """
    Process the uploaded Excel or CSV file.
    
    Args:
        file_path (str): Path to the uploaded file
        
    Returns:
        list: List of dictionaries containing student data
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    try:
        # Read the file based on its extension
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        # Check for required columns
        required_columns = ['Student Name', 'Nationality', 'Program Name', 'Email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Rename columns to standardized format
        df = df.rename(columns={
            'Student Name': 'name',
            'Nationality': 'nationality',
            'Program Name': 'program',
            'Email': 'email'
        })
        
        # Process each row and determine program details
        result = []
        for _, row in df.iterrows():
            # Get program details
            program_details = determine_program_details(row['program'])
            
            # Calculate fee total for first year
            first_year_total = (program_details['one_time_fee'] +
                        program_details['tuition_fee'] +
                        program_details['elp_fee'] +
                        program_details['hostel_fee'])
            
            student_data = {
                'name': row['name'],
                'nationality': row['nationality'],
                'program': row['program'],
                'email': row['email'],
                'program_type': program_details['program_type'],
                'duration': program_details['duration'],
                'tuition_fee': program_details['tuition_fee'],
                'one_time_fee': program_details['one_time_fee'],
                'elp_fee': program_details['elp_fee'],
                'hostel_fee': program_details['hostel_fee'],
                'first_year_total': first_year_total,
                'scholarship': program_details['scholarship'],
                'fee': program_details['tuition_fee']  # For backward compatibility
            }
            result.append(student_data)
        
        return result
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        raise
