from flask import Flask
import logging
from pdfsort_classes import Pdf_serve

# Define paths
from config.config import *

logging.log(logging.DEBUG, "app = Flask defined")

app = Flask(__name__, root_path=ROOT_PATH, template_folder=TEMPLATE_PATH)

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
app = Flask(__name__, root_path=ROOT_PATH, template_folder=TEMPLATE_PATH)
logging.log(logging.DEBUG, "app = Flask defined")