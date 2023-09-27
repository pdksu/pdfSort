#  score_sheet
# read a multi-page .pdf with scanned sheets done by students, score them, assign the scores to individual students
# build a .csv file with the output. The output .csv file should also assist in sorting the .pdf to make sure that
#   1) right students get right scores
#   2) the sheets can be returned to the students 
# but (1) and (2) are outside of the scope of this particular .py file.
#
#  method: read in class list
#    at each page of .pdf, try reading. If successful, assign score and note pages
#    when done, .csv should be written.
#
from flask import Flask, render_template, request, send_file
import cv2
import io
from PIL import Image, ImageDraw, ImageFont
import logging
import numpy as np
import os
import sys
import pandas as pd
# from PyPDF2 import PdfReader
import PyPDF2
import fitz #MuPDF
import sys
from string import ascii_uppercase
from bfind import ArucoBubbleSheet, page_qr

# Define paths
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(os.path.dirname(ROOT_PATH), 'templates')

app = Flask(__name__, root_path=ROOT_PATH, template_folder=TEMPLATE_PATH)
logging.log(logging.DEBUG, "app = Flask defined")

@app.route('/', methods=['GET', 'POST'])
def index():
    logging.log(logging.DEBUG, "index()")
    if request.method == 'POST':
        pdf_file = request.form['pdf']
        scores_dir = request.form['scores']
        return_dir = request.form['returns']
        student_file = request.form['students']
        blank_dir = request.form['blanks']

        pdf = Pdf_serve(pdf_file)

def pixmap_to_pil(pixmap):
    """Convert a PyMuPDF Pixmap to a PIL Image."""
    if pixmap.n == 4:
        mode = "RGBA"
    elif pixmap.n == 3:
        mode = "RGB"
    elif pixmap.n == 1:
        mode = "L"

    return Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)

class Pdf_serve():
    def __init__(self, pdf_file, scale: float = 3.25):
        self.reader = fitz.open(pdf_file)
        self.npages = len(self.reader)
        self.page_index = 0
        self.scale = scale

    def next_qr_page(self):
        scale_matrix = fitz.Matrix(self.scale, self.scale)
        while self.page_index < self.npages: # and (self.page_index < 10):
            qrc_success = False
            page = self.reader[self.page_index]
            pixmap = page.get_pixmap(matrix = scale_matrix)
            if pixmap:
                image = pixmap_to_pil(pixmap)
                qrc_success, qrc = page_qr(image)
                yield (qrc, image) if qrc_success else (None, image)
            self.page_index += 1

def annotate_image(img, text):
    # Open the image and get its size
    width, height = img.size
    
    # Create a drawing context
    draw = ImageDraw.Draw(img)
    
    # Choose a font and size
    font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 80)  # Adjust font path and size accordingly
    
    # Calculate text width and height
    print(text)
    text_width = draw.textlength(text=text, font=font)
    text_height = 140
    
    # Define position to place the text at the bottom-center of the image
    x = (width - text_width) / 2
    y = height - 180  # 10 pixels padding from the bottom
    # Draw a semi-transparent rectangle behind the text for better visibility

    padding = 5
    draw.rectangle([x - padding, y - padding, x + text_width + padding, y + text_height + padding], fill=(255, 255, 255, 128))

    # Draw the text on the image
    draw.text((x, y), text, font=font, fill=(90, 150, 90, 100))  # Change fill color if needed

    return img

def insert_image_to_pdf(image, pdf_file):
    # Convert PIL image to PDF
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PDF')
    img_byte_arr.seek(0)

    # Check if PDF exists
    if not os.path.exists(pdf_file):
        with open(pdf_file, "wb") as f:
            f.write(img_byte_arr.read())
        return

    # If PDF exists, insert the image as the first page
    pdf_writer = PyPDF2.PdfWriter()
    pdf_reader = PyPDF2.PdfReader(pdf_file)

    # Add our image as the first page
    pdf_writer.add_page(PyPDF2.PdfReader(img_byte_arr).pages[0])

    # Add existing PDF pages
    for page_num in range(len(pdf_reader.pages)):
        pdf_writer.add_page(pdf_reader.pages[page_num])

    # Write the combined PDF
    with open(pdf_file, "wb") as f:
        pdf_writer.write(f)

def get_students(student_csv: str = "classlists22.csv"):
    with open(student_csv, 'r') as f:
        reader = pd.read_csv(f)
        return reader

class bubble_sheet():
    def __init__(self, fname,  q_items, name=None):
        self.pdfReader = PdfReader(fname)
        self.scanner = ArucoBubbleSheet(q_items)
        self.name = name

    def scan_page(self, page):
        for img in page.images:
            qrc_success, qrc = page_qr(img.image)
            if not qrc_success:
                continue
            try:
                bubbles = self.scanner.analyze_bubbles(img.image)
            except KeyError as e:
                bubbles = None 
            if bubbles:
                bubbles["name"] = self.name
                return True, bubbles
        return False, {}

Q_ITEMS_DEFAULT =   {"student" : {"items" : {"ID" : {(i, 0) : i for i in range(10)},
                    "SECTION" : {(19+2*i, 0) : 2*(1+i) for i in range(4)},
                    "FIRST_INIT" : {(i, 1 ) : ascii_uppercase[i] for i in range(26)},
                    "LAST_INIT"  : {(i, 2 ) : ascii_uppercase[i] for i in range(26)} },
                    "bounds" :  { "tl" : (0 , (np.max, np.min)), # top left
                                  "bl" : (1 , (np.max, np.max)), # bottom left
                                  "br" : (2 , (np.min, np.max)), # bottom right
                                  "tr" : (3 , (np.min, np.min))  # top right
                                  },
                    "grid" : (26, 3)
                            },
#                "self_assessment10" : {"items" : {"score" : {(i, 0) : i+1 for i in range(10)}},
#                                     "bounds" : { "tl" : (5 , (np.max, np.min)), # top left
#                                                  "bl" : (5 , (np.max, np.max)), # bottom left
#                                                  "br" : (6 , (np.min, np.max)), # bottom right
#                                                  "tr" : (6 , (np.min, np.min)) }, # top right
#                                     "grid" : (11, 1)
#                                    },
#                "assessment10" : {"items" : {"score" : {(i, 0) : i+1 for i in range(10)}},
#                                     "bounds" : { "tl" : (7 , (np.max, np.min)), # top left
#                                                  "bl" : (7 , (np.max, np.max)), # bottom left
#                                                  "br" : (8 , (np.min, np.max)), # bottom right
#                                                  "tr" : (8 , (np.min, np.min)) }, # top right
#                                     "grid" : (11, 1)
#                                    },
                "self_assessment4" : {"items" : {"score" : {(i, 0) : i for i in range(5)}},
                                     "bounds" : { "tl" : (7 , (np.max, np.min)), # top left
                                                  "bl" : (7 , (np.max, np.max)), # bottom left
                                                  "br" : (8 , (np.min, np.max)), # bottom right
                                                  "tr" : (8, (np.min, np.min)) }, # top right
                                     "grid" : (5, 1)
                                    },
                "assessment4" : {"items" : {"score" : {(i, 0) : i for i in range(5)}},
                                     "bounds" : { "tl" : (5, (np.max, np.min)), # top left
                                                  "bl" : (5, (np.max, np.max)), # bottom left
                                                  "br" : (6 , (np.min, np.max)), # bottom right
                                                  "tr" : (6 , (np.min, np.min)) }, # top right
                                     "grid" : (5, 1)
                                    },
}
for item in Q_ITEMS_DEFAULT.keys():
    Q_ITEMS_DEFAULT[item]["set"] = set([b[0] for b in Q_ITEMS_DEFAULT[item]["bounds"].values()])

def best_v(choice_dir : dict = {}, ret_type = str):
    low_p = 1.0
    choice = "_"
    for k, v in choice_dir.items():
        try:
            if v <= low_p:
                low_p = v
                choice = k
        except TypeError as e:
            print(f"{v}--\n{choice_dir}")
            raise e
    return ret_type(choice)

def update_p_val(row, search_data, col_name:str="pageId"):
    rval = row[col_name]
    updated_p = row["p_val"]
    key_order = ["FIRST_INIT","LAST_INIT","ID","SECTION"]

    for i, (char, key) in enumerate(zip(rval, key_order)):
        if char in search_data[key]:
            updated_p *= max(0.01, search_data[key][char])
    return updated_p

# Platform-specific imports and functions
if sys.platform.startswith('win32'):
    import msvcrt

    def get_key():
        """Read single keypress from Windows console."""
        return msvcrt.getch().decode('utf-8')

else:
    import curses

    def get_key():
        """Read single keypress from UNIX console."""
        stdscr = curses.initscr()
        curses.cbreak()
        stdscr.keypad(1)
        stdscr.addstr(0, 10, "Press a key")
        stdscr.refresh()
        key = stdscr.getch()
        curses.endwin()
        return chr(key)

def display_choices(likely_student, page, students):
    if likely_student.shape[0] == 1:
        return likely_student

    page.show()

    # Extract relevant column names
    first_name_col = [col for col in students.columns if col.startswith('First')][0]  # Assuming there's only one column that starts with 'First'
    last_name_col = [col for col in students.columns if col.startswith('Last')][0]  # Assuming there's only one column that starts with 'Last'
    page_index_col = [col for col in students.columns if col.startswith('page')][0]  # Assuming there's only one column that starts with 'Last'
    # Helper function to display choices
    def show_choices(possible_choices, alternative):
        for index, (_, student) in enumerate(possible_choices.iterrows(), 1):
            # Printing only specific fields
            print(f"({index}) {student[first_name_col]} {student[last_name_col]} {student[page_index_col]}")
        print(alternative)

    # Initial display of all likely student choices
    show_choices(likely_student, "(s) Spell")

    # Variable to store the current substring of the name being spelled
    current_string = ""

    first_name_col = [col for col in students.columns if col.startswith('First')][0]  # Assuming there's only one column that starts with 'First'

    # Collect user input until a valid choice is made
    while True:
        choice = input("Enter your choice: ")

        if choice == 's':
            print("Start typing the name [ESC to exit]...")

            current_string = ""
            while True:
                # Get single key stroke
                letter = get_key()
                print(f"got {letter}, {ord(letter)}", flush=True)

                # Use ESC key as exit mechanism, ASCII value for ESC is 27
                if ord(letter) == 27:
                    break

                current_string += letter
                print(f"current string = {current_string}", end='', flush=True)

                # Filter students based on the current substring
                matching_students = students[students[first_name_col].str.lower().str.startswith(current_string.lower(), na=False)]

                if matching_students.empty:
                    print("No matches found. Try again.")
                    current_string = current_string[:-1]  # Remove the last letter
                    continue

                if matching_students.shape[0] < 5:
                    print("")
                    show_choices(matching_students, "")
                    break  # Breaks out of the inner while loop

                print(f"{matching_students.shape[0]} matches found. Keep typing...")

            likely_student = matching_students  # Reset the likely_student DataFrame
            continue  # This continues the outer loop

        if choice.isdigit() and 1 <= int(choice) <= likely_student.shape[0]:
            # Return the chosen student
            return likely_student.iloc[int(choice) - 1:int(choice)]

        print("Invalid choice. Please try again.")

if __name__ == '__main__':
    # --- load student list ------
    results_dir = "/Users/peterkaplan/Code/pdfSort/csv_out/"
    return_dir = "/Users/peterkaplan/Code/pdfSort/pdf_out/"
    student_file = "/Users/peterkaplan/Code/pdfSort/bars/students_from_classroom.csv"
    students = pd.read_csv(student_file)
    if 'pageId' not in students.columns:
        raise KeyError(f"Missing Column: pageId from file {student_file}")
    print(students.columns)
#    students["SchoolId"] = students.ID 
#    students.ID = students.ID % 10
#    students["FIRST_INIT"] = students[[col for col in students.columns if col.startswith('First')][0]].str[0]
#    students["LAST_INIT"] = students[[col for col in students.columns if col.startswith('Last') ][0]].str[0]
#    students.rename(columns={"Section":"SECTION"})

    # ----- get ready to process .pdf file ----
    scanneds= ["hw abc.pdf",
     "Do now abc1.pdf",
     "donow dim anal2 table.pdf", #different aruco
     "donow volume 1.pdf",
     "hw2 dim anal.pdf",
     "do now three sec.pdf"]
    scanned_work = scanneds[5]
    p = Pdf_serve(scanned_work, scale=5)
    i = 0
    aruco_reader = ArucoBubbleSheet(Q_ITEMS_DEFAULT)

    # ------ page loop --------
    reprocess_page_list = []
    found_entries = {}
    print("page: #/MAX: key, self, instructor")
    for (page_title, qr_loc, _), page in p.next_qr_page():
        print(page_title)
        if page_title not in found_entries:
            found_entries[page_title] = {}
        out_csvf = results_dir+page_title+".csv"
        if not os.path.exists(out_csvf):
            with open(out_csvf,"w") as f:
               f.write(",".join(["First","Last","Section","SelfA","ID","Score"])+"\n") 

        i += 1
        if i<64:
            continue
        f_page = cv2.cvtColor(np.array(page), cv2.COLOR_BGR2GRAY)
        f_page = cv2.adaptiveThreshold(f_page, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 75, 2)
#        f_page = cv2.GaussianBlur(f_page, (7, 7), 0) #makes finding worse
        f_page = cv2.dilate(f_page, np.ones((3, 3), np.uint8))
        aruco_dict = aruco_reader.aruco_find(f_page)
        if not aruco_dict:
            aruco_dict = None
        bubble_results, marked_page = aruco_reader.analyze_bubbles(page, ad = aruco_dict)
        try:
            student = bubble_results['student']
            student_key = best_v(student['FIRST_INIT']) + best_v(student['LAST_INIT']) +\
                      best_v(student['ID']) + best_v(student['SECTION'])
            student["ID"] = {str(k):v for k,v in student["ID"].items()}
            student["SECTION"] = {str(k):v for k,v in student["SECTION"].items()}
        except KeyError:
            reprocess_page_list.append(i)
            marked_page.show()
            print(f"::::{i}/{p.npages}: ({page.width}, {page.height}) {page_title[0]} {[k for k in aruco_dict.keys()]} {bubble_results} ::::::")
            continue
        which_student = students[["pageId","First Name","Last Name","Section", "ID"]].copy()
        which_student["p_val"] = 1.0
        which_student.p_val = which_student.apply(lambda row: update_p_val(row, student, col_name="pageId"), axis=1)
        which_student.p_val = which_student.apply(lambda row: row['p_val'] if row['pageId'] not in found_entries[page_title] else row['p_val']*100, axis=1)
        most_likely_p = min(which_student.p_val)
        likely_student = which_student[which_student.p_val <= 10*most_likely_p]
        try:
            likely_student = display_choices(likely_student, page, students).iloc[0] # does nothing if only one choice
        except AttributeError:
            continue
        try:
            print(f'++{i+1}/{p.npages}: {student_key}, {likely_student[["First Name", "Last Name", "Section", "ID"]]}++')
        except TypeError:
            continue 
        results = {key: str(best_v(value["score"])) for key, value in bubble_results.items() if key != "student"}
        print(results)
        try:
          outstr = f'{likely_student["First Name"]}, {likely_student["Last Name"]}, {likely_student["Section"]}, {likely_student["pageId"]}, {results["self_assessment4"]}, {likely_student["ID"]}, {results["assessment4"]}'
        except KeyError as ke:
            if 'self' in str(ke):
                results["self_assessment4"]="_"
            else:
                results["assessment4"] = "_"
        try:
            found_entries[page_title][likely_student.pageId]=likely_student.p_val
        except AttributeError:
            found_entries[page_title][likely_student.pageId]=1e-6
        with open(out_csvf,"a") as f:
            out_str = ",".join([likely_student["First Name"], likely_student["Last Name"], str(likely_student["Section"]),
                              likely_student["pageId"], results["self_assessment4"], 
                              str(likely_student["ID"]), str(results["assessment4"])])
            print(out_str)
            f.write(out_str+"\n")
        out_str = f'{likely_student["First Name"]} {likely_student["Last Name"]}, section {str(likely_student["Section"])}, ID: {str(likely_student["ID"])}, self={results["self_assessment4"]}, instructor={results["assessment4"]} '
        marked_page = annotate_image(marked_page, out_str)
        out_pdff = return_dir + likely_student["pageId"]+"_MP1.pdf"
        insert_image_to_pdf(marked_page, out_pdff)
