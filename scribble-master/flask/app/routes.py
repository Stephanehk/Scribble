import os
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from app import writing_anal

app = Flask(__name__)

UPLOAD_FOLDER = os.path.basename('uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def hello_world():
    return render_template('index.html')

file_names = []

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['image']
    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

    file.save(filename)
    file_names.append(filename)
    if len(file_names) == 2:
        print ("calculating...")
        score = writing_anal.main(file_names[0], file_names[1])
        print (score)
        #os.remove("/Users/2020shatgiskessell/Downloads/scribble-master/flask/app/"+file_names[0])
        #os.remove("/Users/2020shatgiskessell/Downloads/scribble-master/flask/app/"+file_names[1])

    # invalidImage = False
    # if invalidImage:
    #     os.remove(filename)

    return render_template('index.html', invalidImage=False, init=True)
