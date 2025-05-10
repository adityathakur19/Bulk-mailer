document.addEventListener('DOMContentLoaded', function() {
    // Initialize flatpickr for date selection
    flatpickr("#date", {
        dateFormat: "F j, Y", // e.g., "January 1, 2023"
        altInput: true,
        altFormat: "F j, Y",
        defaultDate: new Date()
    });

    // Get DOM elements
    const uploadForm = document.getElementById('uploadForm');
    const resultsSection = document.getElementById('resultsSection');
    const previewTableBody = document.getElementById('previewTableBody');
    const successMessage = document.getElementById('successMessage');
    const generateAllBtn = document.getElementById('generateAllBtn');
    const resetBtn = document.getElementById('resetBtn');
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    const errorMessageEl = document.getElementById('errorMessage');
    const loadingMessageEl = document.getElementById('loadingMessage');

    // Store student data
    let studentData = [];

    // Handle form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();

        // Show loading modal
        loadingMessageEl.textContent = 'Uploading and processing file...';
        loadingModal.show();

        // Create FormData and send request
        const formData = new FormData(uploadForm);
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingModal.hide();
            
            if (data.error) {
                // Show error message
                errorMessageEl.textContent = data.error;
                errorModal.show();
            } else {
                // Update success message
                successMessage.textContent = data.message;
                
                // Store data for later use
                studentData = data.preview;
                
                // Populate the preview table
                populatePreviewTable(data.preview);
                
                // Show results section
                resultsSection.classList.remove('d-none');
                
                // Scroll to results
                resultsSection.scrollIntoView({ behavior: 'smooth' });
            }
        })
        .catch(error => {
            loadingModal.hide();
            errorMessageEl.textContent = 'An unexpected error occurred. Please try again.';
            errorModal.show();
            console.error('Error:', error);
        });
    });

    // Function to populate the preview table
    function populatePreviewTable(data) {
        previewTableBody.innerHTML = '';
        
        data.forEach((student, index) => {
            const row = document.createElement('tr');
            
            // Name cell
            const nameCell = document.createElement('td');
            nameCell.textContent = student.name;
            row.appendChild(nameCell);
            
            // Nationality cell
            const nationalityCell = document.createElement('td');
            nationalityCell.textContent = student.nationality;
            row.appendChild(nationalityCell);
            
            // Program cell
            const programCell = document.createElement('td');
            programCell.textContent = student.program;
            row.appendChild(programCell);
            
            // Fee cell
            const feeCell = document.createElement('td');
            feeCell.textContent = `$${student.fee}`;
            row.appendChild(feeCell);
            
            // Actions cell
            const actionsCell = document.createElement('td');
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn btn-sm btn-outline-primary';
            downloadBtn.innerHTML = '<i class="fas fa-download me-1"></i> Download';
            downloadBtn.addEventListener('click', () => generatePDF(index));
            actionsCell.appendChild(downloadBtn);
            row.appendChild(actionsCell);
            
            previewTableBody.appendChild(row);
        });
    }

    // Function to generate a single PDF
    function generatePDF(index) {
        // Show loading modal
        loadingMessageEl.textContent = 'Generating PDF...';
        loadingModal.show();
        
        const formData = new FormData();
        formData.append('index', index);
        
        fetch('/generate-pdf', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            loadingModal.hide();
            
            if (response.ok) {
                return response.blob();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to generate PDF');
                });
            }
        })
        .then(blob => {
            // Create a URL for the blob
            const url = window.URL.createObjectURL(blob);
            
            // Create a temporary link and trigger download
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `offer_letter_${studentData[index].name.replace(/\s+/g, '_')}.pdf`;
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            loadingModal.hide();
            errorMessageEl.textContent = error.message;
            errorModal.show();
            console.error('Error:', error);
        });
    }

    // Handle "Download All as ZIP" button click
    generateAllBtn.addEventListener('click', function() {
        // Show loading modal
        loadingMessageEl.textContent = 'Generating all PDFs and creating ZIP file...';
        loadingModal.show();
        
        fetch('/generate-all-pdfs', {
            method: 'POST'
        })
        .then(response => {
            loadingModal.hide();
            
            if (response.ok) {
                return response.blob();
            } else {
                return response.json().then(data => {
                    throw new Error(data.error || 'Failed to generate PDFs');
                });
            }
        })
        .then(blob => {
            // Create a URL for the blob
            const url = window.URL.createObjectURL(blob);
            
            // Create a temporary link and trigger download
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'offer_letters.zip';
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            loadingModal.hide();
            errorMessageEl.textContent = error.message;
            errorModal.show();
            console.error('Error:', error);
        });
    });

    // Handle "Reset Form" button click
    resetBtn.addEventListener('click', function() {
        // Reset the form
        uploadForm.reset();
        
        // Hide results section
        resultsSection.classList.add('d-none');
        
        // Clear the preview table
        previewTableBody.innerHTML = '';
        
        // Scroll to top
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});
