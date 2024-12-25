## Navigation:

main file is:
    score_sheet.py
This imports:
    choices.py
    pdfsort_classes.py
    bfind.py

Other files are for different tasks:

merge_scores.py -- combines scores from mulitple files
bmake.py -- used for QR code generator

## Operation

score_sheet [-Q] fname.pdf
    -Q means don't look for a QR code, just process every page.
    -A means don't look for ARUCO codes, just prompt for student name.

### Montclair branch

goals / wishes:

new coding system without numbers, e.g. 1st two letters of both first and last name, last digit of birth-day
improved processing of multiple pages
quicker incorporation of QR code on page
better data merging and tracking, ideally a student dashboard

first steps

coding system clean up

# PDF Sorter Documentation

This documentation is AI generated

### Overview
This project is designed to sort scanned student papers into individual portfolios. The main script, score_sheet.py, processes a multi-page PDF with scanned sheets, scores them, and assigns the scores to individual students. The output is a CSV file with the scores and a sorted PDF for each student.

### Prerequisites
Python Environment: Ensure you have Python 3.9 installed.
Dependencies: Install the required Python packages listed in requirements.txt:
Directory Structure
Ensure your workspace has the following structure:

## Setup Instructions
Student Data: Ensure you have the student data in student_keys.csv. You can generate this file using the gen_student_data.R script.

Scanned PDFs: Place the scanned PDF files in the scans directory.

Configuration: Update the paths in config.py if necessary.

## Running the Script
Navigate to the Source Directory:

Run the Script:

The script will process the scanned PDF files, score them, and generate the output CSV files and sorted PDFs.

Output
CSV Files: The scores will be saved in the csv_out directory.
Sorted PDFs: The sorted PDFs will be saved in the pdf_out directory.
Additional Information
Configuration: The script uses the configuration defined in config.py.
Logging: The script logs its progress and any issues encountered during processing.
Troubleshooting
Missing Columns: Ensure the student CSV file has the required columns: First, Last, Section, pageId, ID.
Dependencies: Ensure all required Python packages are installed.