#  score_sheet pdfsort_classes  key routines for scoring sheets and handling pdfs
#
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
from PIL import Image
import fitz #MuPDF
from bfind import page_qr, page_no_qr

# Define paths
from config.config import *

def pixmap_to_pil(pixmap):
    """Convert a PyMuPDF Pixmap to a PIL Image."""
    if pixmap.n == 4:
        mode = "RGBA"
    elif pixmap.n == 3:
        mode = "RGB"
    elif pixmap.n == 1:
        mode = "L"
    else:
        raise TypeError("No handler written for color encoding with {pixmap.n} channels")
    return Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)

class Pdf_serve():
    def __init__(self, pdf_file, scale: float = 3.25):
        self.reader = fitz.open(pdf_file)
        self.npages = len(self.reader)
        self.page_index = 0
        self.scale = scale
        self.default_page_set = False
        self.default_page = None

    def next_qr_page(self, noQR = False):
        scale_matrix = fitz.Matrix(self.scale, self.scale)
        while self.page_index < self.npages: # and (self.page_index < 10):
            qrc_success = False 
            page = self.reader[self.page_index]
            pixmap = page.get_pixmap(matrix = scale_matrix)
            if pixmap:
                image = pixmap_to_pil(pixmap)
                qrc_success, qrc = page_qr(image) if not noQR else page_no_qr(image)
                if not qrc_success:
                    if not self.default_page_set:
                        default_pagename = input("No QR code found, enter default for this scan file (- for skip page, enter to append to prior)")
                        print(f"New default: {default_pagename}")
                        self.default_page_set = True
                        try:
                            if default_pagename[0] != "-":
                                self.default_page = default_pagename
                        except IndexError:
                            yield((None, None, None), image)
                    qrc = (self.default_page, None, None) # None by default or if leading char is -
                yield (qrc, image)
            self.page_index += 1
