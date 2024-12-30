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
import argparse
import io
from PIL import ImageDraw, ImageFont, Image
import numpy as np
import os
from pandas import read_csv
import PyPDF2
from string import ascii_uppercase
from bfind import ArucoBubbleSheet
from pathlib import Path
from file_lists import list_from_file, files_to_csv
from pdfsort_classes import Pdf_serve 
from choices import display_choices
from typing import Optional, Tuple

# Define paths
from config.config import *


def annotate_image(img, text):
    # Open the image and get its size
    width, height = img.size
    # Create a drawing context
    draw_obj = ImageDraw.Draw(img)
    # Choose a font and size
    font = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 80)  # Adjust font path and size accordingly
    # Calculate text width and height
    print(text)
    text_width = draw_obj.textlength(text=text, font=font)
    text_height = 140
    # Define position to place the text at the bottom-center of the image
    x = (width - text_width) / 2
    y = height - 180  # 10 pixels padding from the bottom
    # Draw a semi-transparent rectangle behind the text for better visibility

    padding = 5
    draw_obj.rectangle([x - padding, y - padding, x + text_width + padding, y + text_height + padding], fill=(255, 255, 255, 128))

    # Draw the text on the image
    draw_obj.text((x, y), text, font=font, fill=(90, 150, 90, 100))  # Change fill color if needed

    return img

def insert_image_to_pdf(image, pdf_file: str, offset: int = 0):
    # Convert PIL image to PDF
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PDF')
    img_byte_arr.seek(0)

    # Check if PDF exists
    if not os.path.exists(pdf_file):
        with open(pdf_file, "wb") as f:
            f.write(img_byte_arr.read())
        return

    # If PDF exists, insert the image as page # offset (from 0) page
    pdf_writer = PyPDF2.PdfWriter()
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    added = 0
    for page_num in range(len(pdf_reader.pages)+1):
        pass
        if page_num == offset:
            # Add our image
            pdf_writer.add_page(PyPDF2.PdfReader(img_byte_arr).pages[0])
            added += 1
        else:
            # Add existing PDF pages
            pdf_writer.add_page(pdf_reader.pages[page_num - added]) 

    # Write the combined PDF
    with open(pdf_file, "wb") as f:
        pdf_writer.write(f)

def get_students(student_csv: str = "classlists22.csv"):
    with open(student_csv, 'r') as f:
        reader = read_csv(f)
        return reader

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
               "self_assessment10" : {"items" : {"score" : {(i, 0) : i for i in range(11)}},
                                    "bounds" : { "tl" : (7 , (np.max, np.min)), # top left
                                                 "bl" : (7 , (np.max, np.max)), # bottom left
                                                 "br" : (8 , (np.min, np.max)), # bottom right
                                                 "tr" : (8 , (np.min, np.min)) }, # top right
                                    "grid" : (11, 1)
                                   },
               "assessment10" : {"items" : {"score" : {(i, 0) : i for i in range(11)}},
                                    "bounds" : { "tl" : (5 , (np.max, np.min)), # top left
                                                 "bl" : (5 , (np.max, np.max)), # bottom left
                                                 "br" : (6 , (np.min, np.max)), # bottom right
                                                 "tr" : (6 , (np.min, np.min)) }, # top right
                                    "grid" : (11, 1)
                                   },
                 "self_assessment4" : {"items" : {"score" : {(i, 0) : i for i in range(5)}},
                                      "bounds" : { "tl" : (11 , (np.max, np.min)), # top left
                                                   "bl" : (11 , (np.max, np.max)), # bottom left
                                                   "br" : (12 , (np.min, np.max)), # bottom right
                                                   "tr" : (12, (np.min, np.min)) }, # top right
                                      "grid" : (5, 1)
                                     },
                 "assessment4" : {"items" : {"score" : {(i, 0) : i for i in range(5)}},
                                      "bounds" : { "tl" : (9, (np.max, np.min)), # top left
                                                   "bl" : (9, (np.max, np.max)), # bottom left
                                                   "br" : (10, (np.min, np.max)), # bottom right
                                                   "tr" : (10, (np.min, np.min)) }, # top right
                                      "grid" : (5, 1)
                                     },
}
for item in Q_ITEMS_DEFAULT.keys():
    Q_ITEMS_DEFAULT[item]["set"] = set([b[0] for b in Q_ITEMS_DEFAULT[item]["bounds"].values()])

def darkest_bubble_str(choice_dir : dict = {}, return_type = str):
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
    return return_type(choice)

def update_p_val(row, search_data: dict, col_name:str="pageId"):
    rval = row[col_name]
    updated_p = row["p_val"]
    key_order = ["FIRST_INIT","LAST_INIT","ID","SECTION"]

    for (char, key) in zip(rval, key_order):
        if char in search_data[key]:
            updated_p *= max(0.01, search_data[key][char])
    return updated_p

def getargs():
    parser = argparse.ArgumentParser(
        prog='PDFsort',
        description='Sort scans of whole classes into individual portfolios for students.'
    )
    parser.add_argument('-q','--noQR',action='store_true')
    parser.add_argument('-a','--noAruco',action='store_true')
    parser.add_argument('-s','--noScore',action='store_true')
    args = parser.parse_args()
    return args

def score_workflow():
    args = getargs()
    noQR = args.noQR if args.noQR else False
    noAruco = args.noAruco if args.noAruco else False
    noScore = args.noScore if args.noScore else False
    # --- load student list ------
    INTERACTIVE = True
    keepWithPrevious = True # flag to put pages without student ID's with the previously read student ID
    curr_dir = Path().absolute()
    results_dir = curr_dir / Path("csv_out") 
    if not Path(results_dir).exists():
        curr_dir = curr_dir.parent
        results_dir = curr_dir / Path("csv_out") 
    return_dir = curr_dir / Path("pdf_out") 
#    student_file = results_dir / Path("students_from_classroom.csv")  # 2023 Clifton
    student_file = curr_dir / Path("annual_setup/student_keys.csv")   # 2024 Montclair
    scan_dir = return_dir / Path("scans")
    pdf_suffix = "_MP2.pdf"

    students = read_csv(student_file)
    if 'pageId' not in students.columns:
        raise KeyError(f"Missing Column: pageId from file {student_file}")
    print(students.columns)

    # ----- get ready to process .pdf file ----
    files_to_csv(Path(scan_dir)) # update list of scanned files
    scanneds = list_from_file(Path(scan_dir, "scans.csv"))
    scanneds.sort(key=lambda x: os.path.getmtime(str(Path(scan_dir) / x)), reverse=True)
    scanned_work = Path(scan_dir,scanneds[0])  # Take the newest file
    default_file = scanned_work.with_name(scanned_work.stem + "_unproc.pdf")
    likely_student = None
    pdf_page_service = Pdf_serve(scanned_work, scale=5)
    aruco_reader = ArucoBubbleSheet(Q_ITEMS_DEFAULT)

    # ------ page loop --------
    reprocess_page_list = []
    found_entries = {}
    i = 0
    offset = 0
    current_student = None
    current_title = None
    MAX_PAGE_COUNT = 800
    last_choice = None
    print("page: #/MAX: key, self, instructor")
    #  get page_title (from QR code) and page: PIL.Image.Image
    for (page_title, qr_loc, _), page in pdf_page_service.next_qr_page(noQR):  # type: Tuple[Optional[Tuple[Optional[str], Optional[str], Optional[str]]], Image.Image]
        if i >= MAX_PAGE_COUNT:
            i += 1
            continue
        if page_title:
            current_title = page_title
        else:
            if noQR:
                current_title = "No QR Code"  # TODO: prompt user for title
            else:
                current_title = input("Enter title for page: ")
                if not current_title or current_title == "":
                    current_title = "DEFAULT"
        print(page_title)
        out_csvf = results_dir / Path(page_title+".csv")
        found_entries[page_title] = {"file":out_csvf}
        aruco_dict = aruco_reader.aruco_find(page, preprocess=["threshold", "dilate"]) if not noAruco else None
#        if not os.path.exists(out_csvf):
#            with open(out_csvf,"w") as f:
#                f.write(",".join(["First","Last","Section","pageId","ID","Score","SelfA"])+"\n") 
        if aruco_dict:
            bubble_results, marked_page = aruco_reader.analyze_bubbles(page, ad = aruco_dict)
            page = marked_page
        else:
            noAruco = True
        student_info = identify_student(students, page, bubble_results, noAruco)
        if page_title and not noAruco:
            i += 1
            if not aruco_dict:
                aruco_dict = None
            else:
            try:
                print(f'++{i+1}/{pdf_page_service.npages}: {student_key}, {likely_student[["First Name", "Last Name", "Section", "ID"]]}++')
            except TypeError:
                continue
            except UnboundLocalError:
                pass

            def get_values_for_prefix(d: dict, prefix: str, default: str="_"):
                """Retrieve the values of all keys that start with a given prefix."""
                try:
                    values = [value for key, value in d.items() if key.startswith(prefix)]
                except AttributeError: 
                    values = None
                return values if values else [default]

            results = {key: str(darkest_bubble_str(value["score"])) for key, value in bubble_results.items() if key != "student"}
            assessment_str = ", ".join(get_values_for_prefix(results, "assessment"))
            self_assessment_str = ", ".join(get_values_for_prefix(results, "self_assessment"))
            outstr = f'{likely_student["First Name"]}, {likely_student["Last Name"]}, {likely_student["Section"]}, {likely_student["pageId"]}, {likely_student["ID"]}, {assessment_str}, {self_assessment_str}'
            try:
                found_entries[page_title][likely_student.pageId]=likely_student.p_val
            except AttributeError:
                found_entries[page_title][likely_student.pageId]=1e-6
            with open(out_csvf,"a") as f:
                print(outstr)
                f.write(outstr+"\n")
            marked_page = annotate_image(marked_page, outstr)
            out_pdff = Path(return_dir,  likely_student["pageId"]+pdf_suffix)
        else:
            marked_page = page
            out_pdff = default_file
            try:
                likely_student = students[["pageId","First Name","Last Name","Section", "ID"]].copy()
            except KeyError:
                likely_student = students[["pageId","First","Last","Section", ]].copy()
            likely_student = display_choices(likely_student, page, students, interactive=INTERACTIVE, last_choice=last_choice)
            if likely_student.empty:
                out_pdff = default_file
                marked_page = page
            else:
                try:
                    if last_choice["pageId"].values[0] != likely_student["pageId"].values[0]:
                        offset = 0
                except TypeError:
                    offset = 0
                last_choice = likely_student.iloc[0:1]
                likely_student = likely_student.iloc[0]
                out_pdff = Path(return_dir,  likely_student["pageId"]+pdf_suffix)

        insert_image_to_pdf(marked_page, out_pdff, offset = offset) # if no QR code, just stick it where the last page went.
        offset += 1

def identify_student(students, page, bubble_results, noAruco):
    try:
        student = bubble_results['student']
        student["ID"] = {str(k):v for k,v in student["ID"].items()}
        student["SECTION"] = {str(k):v for k,v in student["SECTION"].items()}
    except (TypeError, KeyError):
                pass
    which_student = students[["pageId","First Name","Last Name","Section", "ID"]].copy()
    which_student["p_val"] = 1.0
    which_student.p_val = which_student.apply(lambda row: update_p_val(row, student, col_name="pageId"), axis=1)
    which_student.p_val = which_student.apply(lambda row: row['p_val'] if row['pageId'] not in found_entries[page_title] else row['p_val']*100, axis=1) # try to avoid duplicate pages for the same student
    most_likely_p = min(which_student.p_val)
    likely_student = which_student[which_student.p_val <= 10*most_likely_p]
    try:
        likely_student = display_choices(likely_student, page, students, interactive=INTERACTIVE, last_choice=last_choice)
        if likely_student.empty:
            out_pdff = default_file
            marked_page = page
            continue
        try:
            if last_choice["pageId"] != likely_student["pageId"].values[0]:
                offset = 0
        except TypeError:
            offset = 0
        last_choice = likely_student.iloc[0:1]
        likely_student = likely_student.iloc[0]
    except AttributeError:
        continue
    except ValueError:
        continue
    # Logic to identify student using Aruco bubbles
    pass
if __name__ == '__main__':
    score_workflow()