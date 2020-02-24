

import sys
import os
from argparse import ArgumentParser
import cv2
import time
import logging as log
import tensorflow as tf
import numpy as np
import mysql.connector as sql
from multiprocessing import Process,Manager,Value,Queue
import subprocess
import requests
import json
from datetime import datetime
import pandas as pd
from flask import Flask, jsonify ,request,Response,send_file,render_template
import base64
from flask_cors import CORS
from flask_cors import cross_origin
import skimage.io
from imageio import imread
import re
from random import seed
from random import random
import mysql.connector as sql
from skimage import exposure
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vnkdjnfjknfl1232#'
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

def gen(cap):
    while True:
        success, frame = cap.read()
        flag = 0
        
        image=frame.copy()
        ret,jpeg = cv2.imencode('.jpg',image)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


@app.route('/video_feed/',methods=['get'])
def sendVideoStream():
    global capture
    capture = cv2.VideoCapture(0)
    return Response(gen(capture),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/stopvideo", methods=['post'])
@cross_origin()
def startStopFlag():
    try:
        capture.release()
        status={"status":200}
    except  Exception as e:
        status={"status":500,"result":str(e)}
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002,debug=False)
    