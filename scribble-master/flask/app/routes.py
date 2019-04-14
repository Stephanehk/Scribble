import os
from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from app import writing_anal
import cv2

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
        display_images_names = []
        print ("calculating...")
        score, message, image_with_rects_b, image_with_rects_a = writing_anal.main(file_names[0], file_names[1])
        print (score)
        os.remove(file_names[0])
        os.remove(file_names[1])

        cv2.imwrite(os.path.join("static/public/img" , 'image_b.jpg'), image_with_rects_b)
        #file.save(image_b_f)

        cv2.imwrite(os.path.join("static/public/img" , 'image_a.jpg'), image_with_rects_a)
        #file.save(image_a_f)
        return render_template('index.html', invalidImage=False, output_message=message, image_b = "../static/public/img/image_b.jpg", image_a =  "../static/public/img/image_a.jpg")


    # invalidImage = False
    # if invalidImage:
    #     os.remove(filename)

    return render_template('index.html', invalidImage=False, init=True)
