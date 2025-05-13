document.addEventListener('DOMContentLoaded', function() {
    // Initialize flatpickr for offer date selection
    flatpickr("#date", {
        dateFormat: "d-m-Y", // e.g., "07-05-2025"
        altInput: true,
        altFormat: "d-m-Y",
        defaultDate: new Date()
    });
    
    // Initialize flatpickr for start date selection (month/year only)
    flatpickr("#start_date", {
        dateFormat: "F Y", // e.g., "May 2025"
        altInput: true,
        altFormat: "F Y",
        defaultDate: new Date(),
        plugins: [
            new monthSelectPlugin({
                shorthand: true,
                dateFormat: "F Y",
                altFormat: "F Y"
            })
        ]
    });

    // Get DOM elements
    const uploadForm = document.getElementById('uploadForm');
    const resultsSection = document.getElementById('resultsSection');
    const previewTableBody = document.getElementById('previewTableBody');
    const successMessage = document.getElementById('successMessage');
    const generateAllBtn = document.getElementById('generateAllBtn');
    const sendAllEmailsBtn = document.getElementById('sendAllEmailsBtn');
    const resetBtn = document.getElementById('resetBtn');
    const loadingModal = new bootstrap.Modal(document.getElementById('loadingModal'));
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    const successModal = new bootstrap.Modal(document.getElementById('successModal'));
    const emailResultsModal = new bootstrap.Modal(document.getElementById('emailResultsModal'));
    const errorMessageEl = document.getElementById('errorMessage');
    const successModalMessageEl = document.getElementById('successModalMessage');
    const emailResultsSummaryEl = document.getElementById('emailResultsSummary');
    const emailResultsTableBodyEl = document.getElementById('emailResultsTableBody');
    const loadingMessageEl = document.getElementById('loadingMessage');

    // Store student data
    let studentData = [];
    let currentDataId = null; // Store the current data_id
    const rowsPerPage = 10;
    let currentPage = 1;

    function renderTable() {
        const start = (currentPage - 1) * rowsPerPage;
        const pageItems = studentData.slice(start, start + rowsPerPage);
        populatePreviewTable(pageItems);
        renderPagination();
    }

    // create pagination buttons
    function renderPagination() {
        const pageCount = Math.ceil(studentData.length / rowsPerPage);
        const container = document.getElementById('paginationControls');
        container.innerHTML = '';
        
        // Add "Previous" button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        const prevA = document.createElement('a');
        prevA.className = 'page-link';
        prevA.href = '#';
        prevA.textContent = 'Previous';
        prevA.setAttribute('aria-label', 'Previous');
        prevA.addEventListener('click', e => {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                renderTable();
            }
        });
        prevLi.appendChild(prevA);
        container.appendChild(prevLi);
        
        // Calculate range of pages to show
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(pageCount, startPage + 4);
        
        // Adjust startPage if we're at the end
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        // Create page number buttons
        for (let p = startPage; p <= endPage; p++) {
            const li = document.createElement('li');
            li.className = `page-item ${p === currentPage ? 'active' : ''}`;
            const a = document.createElement('a');
            a.className = 'page-link';
            a.href = '#';
            a.textContent = p;
            a.addEventListener('click', e => {
                e.preventDefault();
                currentPage = p;
                renderTable();
            });
            li.appendChild(a);
            container.appendChild(li);
        }
        
        // Add "Next" button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === pageCount ? 'disabled' : ''}`;
        const nextA = document.createElement('a');
        nextA.className = 'page-link';
        nextA.href = '#';
        nextA.textContent = 'Next';
        nextA.setAttribute('aria-label', 'Next');
        nextA.addEventListener('click', e => {
            e.preventDefault();
            if (currentPage < pageCount) {
                currentPage++;
                renderTable();
            }
        });
        nextLi.appendChild(nextA);
        container.appendChild(nextLi);
    }

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
                errorMessageEl.textContent = data.error;
                errorModal.show();
            } else {
                // Store the data_id for future requests
                currentDataId = data.data_id;
                
                studentData = data.preview;   // now contains all records
                currentPage = 1;              // reset to first page
                document.getElementById('successMessage').textContent = data.message;
                renderTable();                // initial render
                resultsSection.classList.remove('d-none');
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
    function populatePreviewTable(dataArray) {
        previewTableBody.innerHTML = '';
        dataArray.forEach((student, index) => {
            const row = document.createElement('tr');
            
            // Calculate the actual global index based on current page
            const globalIndex = (currentPage - 1) * rowsPerPage + index;
            
            // Name cell
            const nameCell = document.createElement('td');
            nameCell.textContent = student.name;
            row.appendChild(nameCell);
            
            // Email cell
            const emailCell = document.createElement('td');
            emailCell.textContent = student.email;
            row.appendChild(emailCell);
            
            // Nationality cell
            const nationalityCell = document.createElement('td');
            nationalityCell.textContent = student.nationality;
            row.appendChild(nationalityCell);
            
            // Program cell
            const programCell = document.createElement('td');
            programCell.textContent = student.program;
            row.appendChild(programCell);
            
            // Duration cell
            const durationCell = document.createElement('td');
            durationCell.textContent = student.duration;
            row.appendChild(durationCell);
            
            // Tuition Fee cell
            const tuitionFeeCell = document.createElement('td');
            tuitionFeeCell.textContent = `$${student.tuition_fee}`;
            row.appendChild(tuitionFeeCell);
            
            // First Year Total cell
            const totalFeeCell = document.createElement('td');
            totalFeeCell.textContent = `$${student.first_year_total}`;
            row.appendChild(totalFeeCell);
            
            // Actions cell with both download and email buttons
            const actionsCell = document.createElement('td');
            
            // Download button
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'btn btn-sm btn-outline-primary me-1';
            downloadBtn.innerHTML = '<i class="fas fa-download me-1"></i> Download';
            downloadBtn.addEventListener('click', () => generatePDF(globalIndex));
            actionsCell.appendChild(downloadBtn);
            
            // Email button (if email exists)
            if (student.email) {
                const emailBtn = document.createElement('button');
                emailBtn.className = 'btn btn-sm btn-outline-success';
                emailBtn.innerHTML = '<i class="fas fa-envelope me-1"></i> Email';
                emailBtn.addEventListener('click', () => sendEmail(globalIndex));
                actionsCell.appendChild(emailBtn);
            }
            
            row.appendChild(actionsCell);
            
            previewTableBody.appendChild(row);
        });
    }

    // Function to generate a single PDF
    function generatePDF(index) {
        // Show loading modal
        loadingMessageEl.textContent = 'Generating PDF...';
        loadingModal.show();
        
        // Check if we have a data_id
        if (!currentDataId) {
            loadingModal.hide();
            errorMessageEl.textContent = 'No data ID available. Please upload a file first.';
            errorModal.show();
            return;
        }
        
        const formData = new FormData();
        formData.append('index', index);
        formData.append('data_id', currentDataId);  // Add the data_id
        
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
    
    // Function to send an email with the offer letter
    function sendEmail(index) {
        // Show loading modal
        loadingMessageEl.textContent = 'Sending email...';
        loadingModal.show();
        
        // Check if we have a data_id
        if (!currentDataId) {
            loadingModal.hide();
            errorMessageEl.textContent = 'No data ID available. Please upload a file first.';
            errorModal.show();
            return;
        }
        
        const formData = new FormData();
        formData.append('index', index);
        formData.append('data_id', currentDataId);  // Add the data_id
        
        fetch('/send-email', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingModal.hide();
            
            if (data.error) {
                errorMessageEl.textContent = data.error;
                errorModal.show();
            } else {
                // Create and show success message
                successModalMessageEl.textContent = data.message;
                successModal.show();
                
                // Update the button to show it was sent
                const pageIndex = index % rowsPerPage; // Get the index within the current page
                const row = previewTableBody.children[pageIndex];
                const emailBtn = row.querySelector('.btn-outline-success');
                if (emailBtn) {
                    emailBtn.classList.remove('btn-outline-success');
                    emailBtn.classList.add('btn-success');
                    emailBtn.innerHTML = '<i class="fas fa-check me-1"></i> Sent';
                    emailBtn.disabled = true;
                }
            }
        })
        .catch(error => {
            loadingModal.hide();
            errorMessageEl.textContent = 'An unexpected error occurred. Please try again.';
            errorModal.show();
            console.error('Error:', error);
        });
    }

    // Handle "Download All as ZIP" button click
    generateAllBtn.addEventListener('click', function() {
        // Show loading modal
        loadingMessageEl.textContent = 'Generating all PDFs and creating ZIP file...';
        loadingModal.show();
        
        // Check if we have a data_id
        if (!currentDataId) {
            loadingModal.hide();
            errorMessageEl.textContent = 'No data ID available. Please upload a file first.';
            errorModal.show();
            return;
        }
        
        const formData = new FormData();
        formData.append('data_id', currentDataId);  // Add the data_id
        
        fetch('/generate-all-pdfs', {
            method: 'POST',
            body: formData
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
        
        // Clear student data and data_id
        studentData = [];
        currentDataId = null;
        
        // Scroll to top
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // Handle "Send All Emails" button click
    sendAllEmailsBtn.addEventListener('click', function() {
        // Show loading modal
        loadingMessageEl.textContent = 'Sending emails to all students...';
        loadingModal.show();
        
        // Check if we have a data_id
        if (!currentDataId) {
            loadingModal.hide();
            errorMessageEl.textContent = 'No data ID available. Please upload a file first.';
            errorModal.show();
            return;
        }
        
        const formData = new FormData();
        formData.append('data_id', currentDataId);  // Add the data_id
        
        fetch('/send-all-emails', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            loadingModal.hide();
            
            if (data.error) {
                errorMessageEl.textContent = data.error;
                errorModal.show();
            } else {
                // Show email results
                emailResultsSummaryEl.textContent = data.message;
                
                // Clear previous results
                emailResultsTableBodyEl.innerHTML = '';
                
                // Populate email results table
                if (data.details && data.details.length > 0) {
                    data.details.forEach(result => {
                        const row = document.createElement('tr');
                        
                        // Name cell
                        const nameCell = document.createElement('td');
                        nameCell.textContent = result.name;
                        row.appendChild(nameCell);
                        
                        // Email cell
                        const emailCell = document.createElement('td');
                        emailCell.textContent = result.email;
                        row.appendChild(emailCell);
                        
                        // Status cell
                        const statusCell = document.createElement('td');
                        if (result.status === 'sent') {
                            statusCell.innerHTML = '<span class="badge bg-success">Sent</span>';
                        } else {
                            statusCell.innerHTML = '<span class="badge bg-danger">Failed</span>';
                        }
                        row.appendChild(statusCell);
                        
                        emailResultsTableBodyEl.appendChild(row);
                    });
                }
                
                // Show email results modal
                emailResultsModal.show();
                
                // Update UI to show emails were sent
                renderTable(); // Re-render the current page to show updated button states
            }
        })
        .catch(error => {
            loadingModal.hide();
            errorMessageEl.textContent = 'An unexpected error occurred. Please try again.';
            errorModal.show();
            console.error('Error:', error);
        });
    });
});