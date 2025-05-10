import pandas as pd
import os
import logging

def determine_fee(program_name):
    """
    Determine the fee based on the program type.
    
    Args:
        program_name (str): The name of the program
        
    Returns:
        int: The fee amount
    """
    program_name = program_name.lower()
    
    if any(keyword in program_name for keyword in ['bachelor', 'undergraduate', 'bsc', 'ba', 'beng']):
        return 1000
    elif any(keyword in program_name for keyword in ['master', 'msc', 'ma', 'meng', 'mba']):
        return 1500
    elif any(keyword in program_name for keyword in ['phd', 'doctorate', 'doctoral']):
        return 2000
    else:
        # Default to Bachelor's fee if program type is unclear
        logging.warning(f"Could not determine program type for: {program_name}. Defaulting to Bachelor's fee.")
        return 1000

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
        required_columns = ['Student Name', 'Nationality', 'Program Name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Rename columns to standardized format
        df = df.rename(columns={
            'Student Name': 'name',
            'Nationality': 'nationality',
            'Program Name': 'program'
        })
        
        # Process each row and determine fee
        result = []
        for _, row in df.iterrows():
            student_data = {
                'name': row['name'],
                'nationality': row['nationality'],
                'program': row['program'],
                'fee': determine_fee(row['program'])
            }
            result.append(student_data)
        
        return result
    
    except Exception as e:
        logging.error(f"Error processing file: {str(e)}")
        raise
