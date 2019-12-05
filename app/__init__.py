# Import standard libraries
import os
import io
import json
import uuid
import pickle
import argparse
import numpy as np
import pandas as pd

# Import flask and necessary modules
from flask import Flask, flash, request, render_template, redirect, url_for, \
                  send_from_directory, session
from werkzeug.utils import secure_filename

# Import databse
from app.database import db

# Import Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types


# Read app secret key from text file
with open('app/secret_key.txt', 'r') as f:
    secret_key = f.read().strip()

# Read database credentials from json file
with open('app/db_creds.json') as json_file:
    db_creds = json.load(json_file)

# Define paths and file extensions for app
project_root = os.path.dirname(os.path.realpath('__file__'))
template_path = os.path.join(project_root, 'app/templates')
static_path = os.path.join(project_root, 'app/static')
UPLOAD_FOLDER = os.path.join(static_path, 'inventory')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize app
app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = \
    f"mysql+pymysql://{db_creds['username']}:{db_creds['password']}@localhost/ncr"

# Initialize database
with app.app_context():
    db.init_app(app)
    db.Model.metadata.reflect(db.engine)
    from app.database import models

# Initialize Google Vision API
credentials_file = os.path.join(project_root, 'app/google_vision_api_creds.json')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
client = vision.ImageAnnotatorClient()


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        tag = request.form['input']

        if tag == '':
            return redirect(url_for('index'))
        else:
            filenames = models.Inventory_T.get_items_by_tag(tag)
            return render_template('index.html', title=tag.capitalize(), filenames=filenames)
    else:
        filenames = models.Inventory_T.get_all_items()
        return render_template('index.html', title='All Items', filenames=filenames)


@app.route('/employee_login', methods=['GET', 'POST'])
def employee_login():

    if session.get('logged_in'):

        return redirect(url_for('employees'))

    else:

        if request.method == 'POST':
            verified, response = models.Users_T.verify_user(request.form['username'],
                                                            request.form['password'])
            if verified:
                session['logged_in'] = True
                return redirect(url_for('employees'))
            else:
                flash(response)
                return render_template('employee_login.html')

        else:
            return render_template('employee_login.html')


@app.route('/employees', methods=['GET', 'POST'])
def employees():

    if session.get('logged_in'):

        if request.method == 'POST':

            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit an empty part without filename

            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f'{uuid.uuid1()}.jpg'
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('uploaded_file',
                                        filename=filename))
        else:
            return render_template('employees.html')

    else:
        return redirect(url_for('employee_login'))


@app.route('/employees/uploads/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):

    if request.method == 'POST':
        selections = [val.lower() for key, val in request.form.items(multi=True) if key=='select']
        inputs_string = request.form['input']
        if inputs_string:
            inputs = [item.strip() for item in inputs_string.split(',')]
        else:
            inputs = []
        tags = list(selections) + list(inputs)
        models.Inventory_T.add_items(filename, tags)
        return redirect(url_for('employees'))

    else:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with io.open(filepath, 'rb') as image_file:
            content = image_file.read()
        image = types.Image(content=content)
        response = client.label_detection(image=image)
        #with open ('response.txt', 'rb') as f:
        #   response = pickle.load(f)
        top_matches = [(label.description, label.score) for label in response.label_annotations if label.score > 0.9]
        return render_template('uploaded_file.html', filename=filename, top_matches=top_matches)


if __name__ == '__main__':
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--secret_key_path', type=str, default='secret_key.txt', help='Path to app secret key')
    # parser.add_argument('--templates_path', type=str, default='app/templates', help='Path to templates folder')
    # parser.add_argument('--static_path', type=str, default='app/static', help='Path to static folder')
    # parser.add_argument('--upload_folder', type=str, default='inventory', help='Folder to store uploaded images')
    # parser.add_argument('--google_creds_path', type=str, default='google_vision_api_creds.json', help='Path to JSON file containing Google Vision API credentials')
    # parser.add_argument('--classifier', type=str, default='predictAction', help='Classifier to use for prediction')
    # args = parser.parse_args()

    app.run(debug=True)
