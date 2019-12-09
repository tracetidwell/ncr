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
with open('app/creds/secret_key.txt', 'r') as f:
    secret_key = f.read().strip()

# Read database credentials from json file
with open('app/creds/db_creds.json') as json_file:
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
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_creds['username']}:{db_creds['password']}@localhost/ncr"

# Initialize database
with app.app_context():

    db.init_app(app)
    db.Model.metadata.reflect(db.engine)
    from app.database import models

# Initialize Google Vision API
credentials_file = os.path.join(project_root, 'app/creds/google_vision_api_creds.json')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
client = vision.ImageAnnotatorClient()


def allowed_file(filename: str) -> bool:
    """Checks to see if file extension is allowed

    Parameters
    ----------
    filename : str
    		   Username as a string

    Returns
    -------
    allowed : bool
    		 Boolean indicating whether file extension is in approved list
    """

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index() -> str:
    """Homepage for app
    """

    # Display items by tag (search by user)
    if request.method == 'POST':

        # Get tag from form
        tag = request.form['input']

        # If tag is empty, return default homepage
        if tag == '':
            return redirect(url_for('index'))

        # Otherwise, get all images with specified tag to display
        else:
            filenames = models.Inventory_T.get_items_by_tag(tag)
            return render_template('index.html', title=tag.capitalize(), filenames=filenames)

    # Display all items (default)
    else:
        filenames = models.Inventory_T.get_all_items()
        return render_template('index.html', title='All Items', filenames=filenames)


@app.route('/employee_login', methods=['GET', 'POST'])
def employee_login() -> str:
    """Login page for employees
    """

    # If employee is already logged in, redirect to employees page
    if session.get('logged_in'):
        return redirect(url_for('employees'))

    # Otherwise, check if request was GET or POST
    else:

        # If POST, verify employee
        if request.method == 'POST':
            verified, response = models.Users_T.verify_user(request.form['username'],
                                                            request.form['password'])

            # If verification passes, log employee in and redirect to employee page
            if verified:
                session['logged_in'] = True
                return redirect(url_for('employees'))
            # Otherwise, display reason for failed login
            else:
                flash(response)
                return render_template('employee_login.html')

        # If GET, display login page
        else:
            return render_template('employee_login.html')


@app.route('/employee_logout')
def employee_logout() -> str:
    """Logout page for employees
    """

    # Change logged_in status of session
    session['logged_in'] = False
    # Redirecto to employee login page
    return render_template('employee_login.html')


@app.route('/employees', methods=['GET', 'POST'])
def employees() -> str:
    """Main page for employees
    """

    # Employees must be logged in to view this page
    if session.get('logged_in'):

        # If POST request, employee wants to upload image
        if request.method == 'POST':

            # Check if the post request has the file part
            if 'file' not in request.files:

                flash('No file part')
                return redirect(request.url)

            file = request.files['file']

            # Check if user actually selected a file
            if file.filename == '':

                flash('No selected file')
                return redirect(request.url)

            # Verify file extension is allowed
            if file and allowed_file(file.filename):

                # If so, create a unique, secure filename, upload it to designated upload folder, and redirect to uploads page
                filename = secure_filename(file.filename)
                filename = f'{uuid.uuid1()}.jpg'
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                return redirect(url_for('uploaded_file',
                                        filename=filename))

        # If GET request, display form for selecting an image to upload
        else:
            return render_template('employees.html')

    # If not logged in, redirect to employee login page
    else:
        return redirect(url_for('employee_login'))


@app.route('/employees/uploads/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename: str) -> str:
    """Display results of image classification and labeling
    """

    # If POST request, get tags and store in database
    if request.method == 'POST':
        # Get tags selected by employee
        selections = [val.lower() for key, val in request.form.items(multi=True) if key=='select']
        # Get custom tags input by employee
        inputs_string = request.form['input']
        if inputs_string:
            inputs = [item.strip() for item in inputs_string.split(',')]
        else:
            inputs = []
        # Combine selected and custom tags and add to database with uploaded image
        tags = list(selections) + list(inputs)
        models.Inventory_T.add_item(filename, tags)
        return redirect(url_for('employees'))


    # If GET request, display uploaded image and output tags from model
    else:
        # Load uploaded image from disk and prepare to be sent to Google Vision API
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with io.open(filepath, 'rb') as image_file:
            content = image_file.read()
        image = types.Image(content=content)
        # Get response from Google Vision API
        response = client.label_detection(image=image)
        # Keep all tags with a score > 0.9
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
