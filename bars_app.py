
import base64
from io import BytesIO
from flask import Flask, render_template, request
import os
from source.bmake import mbar

import logging
logging.basicConfig(level=logging.DEBUG)
logging.log(logging.DEBUG, "logging start")

# Define paths
ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(os.path.dirname(ROOT_PATH), 'templates')

app = Flask(__name__) # , root_path=ROOT_PATH, template_folder=TEMPLATE_PATH)
logging.log(logging.DEBUG, "app = Flask defined")

@app.route('/', methods=['GET', 'POST'])
def index():
    logging.log(logging.DEBUG, "index()")
    if request.method == 'POST':
        message = request.form['message']
        im = mbar(message, type='PIL', resize=True, width=120, height=120)
        img_io = BytesIO()
        im.save(img_io, 'PNG')
        img_io.seek(0)
        img_data = base64.b64encode(img_io.getvalue()).decode('utf-8')
        return render_template('qrindex.html', img_data=img_data, img_name=message)
    return render_template('qrindex.html')

if __name__ == '__main__':
    logging.log(logging.DEBUG, "__main__")
    app.run(debug=True)
