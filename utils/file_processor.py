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
        'hostel_fee': 1000,  # Default hostel fee
        'one_time_fee': 500,  # Default one-time fee
        'program_type': ''
    }
    
    # Check for specific engineering programs that are 4 years
    engineering_programs = [
        'b.tech', 'btech', 'bachelor of technology', 'bachelor of engineering', 
        'b.e', 'be', 'beng', 'mechanical engineering', 'civil engineering', 
        'electrical engineering', 'computer engineering', 'computer science'
    ]
    
    # Foundation or Pathway keywords
    foundation_keywords = ['foundation', 'pathway', 'preparatory']
    
    # Bachelor's degree keywords for 3-year programs
    bachelor_3yr_keywords = [
        'bachelor of arts', 'bachelor of science', 'bachelor of commerce',
        'ba', 'bsc', 'bcom', 'b.a', 'b.sc', 'b.com', 'bba', 'b.b.a', 
        'bachelor of business'
    ]
    
    # Bachelor's degree keywords (general)
    all_bachelor_keywords = engineering_programs + bachelor_3yr_keywords + ['bachelor', 'undergraduate']
    
    # Master's degree keywords
    master_keywords = [
        'master', 'msc', 'ma', 'meng', 'mba', 'm.tech', 'mtech', 'mca', 
        'm.sc', 'm.a', 'm.com', 'mcom', 'ms', 'post graduate', 'pg'
    ]
    
    # PhD keywords
    phd_keywords = ['phd', 'doctorate', 'doctoral', 'ph.d', 'doctor of philosophy']
    
    # Diploma keywords
    diploma_keywords = ['diploma', 'certificate', 'pgd', 'post graduate diploma']
    
    # BCA and MCA specific check
    is_bca = 'bca' in program_name or 'bachelor of computer application' in program_name
    is_mca = 'mca' in program_name or 'master of computer application' in program_name
    
    # Determine program type and set details
    has_foundation = any(keyword in program_name for keyword in foundation_keywords)
    is_engineering = any(keyword in program_name for keyword in engineering_programs)
    
    # Specific program type identification with appropriate duration
    if is_engineering or is_bca or any(program_name.startswith(kw) for kw in ['b.tech', 'btech']):
        result['tuition_fee'] = 1600
        result['duration'] = '04 YEARS'
        result['program_type'] = 'Bachelor'
    elif any(keyword in program_name for keyword in bachelor_3yr_keywords):
        result['tuition_fee'] = 1600
        result['duration'] = '03 YEARS'
        result['program_type'] = 'Bachelor'
    elif any(keyword in program_name for keyword in all_bachelor_keywords):
        # General bachelor's (if not caught by more specific rules)
        result['tuition_fee'] = 1600
        result['duration'] = '03 YEARS'
        result['program_type'] = 'Bachelor'
    elif is_mca:
        result['tuition_fee'] = 1800
        result['duration'] = '02 YEARS'
        result['program_type'] = 'Master'
    elif any(keyword in program_name for keyword in master_keywords):
        result['tuition_fee'] = 1800
        result['duration'] = '02 YEARS'
        result['program_type'] = 'Master'
    elif any(keyword in program_name for keyword in phd_keywords):
        result['tuition_fee'] = 2000
        result['duration'] = '03 YEARS'
        result['program_type'] = 'PhD'
    elif any(keyword in program_name for keyword in diploma_keywords):
        result['tuition_fee'] = 1200
        result['duration'] = '01 YEAR'
        result['program_type'] = 'Diploma'
    else:
        # Default to Bachelor's fee if program type is unclear
        logging.warning(f"Could not determine program type for: {program_name}. Defaulting to Bachelor's details.")
        result['tuition_fee'] = 1600
        result['duration'] = '03 YEARS'
        result['program_type'] = 'Bachelor'
    
    # If program has foundation, add a year to bachelor programs
    if has_foundation and result['program_type'] == 'Bachelor':
        # If it's already a 4-year program, keep it at 4 years
        # For 3-year programs with foundation, make it 4 years
        if result['duration'] == '03 YEARS':
            result['duration'] = '04 YEARS'
    
    # Determine scholarship (could be expanded based on criteria)
    result['scholarship'] = "CHANCELLOR'S Scholarship"
    
    # English Language Program (ELP) fee
    result['elp_fee'] = 500 if has_foundation or 'english' in program_name.lower() else 0
    
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
