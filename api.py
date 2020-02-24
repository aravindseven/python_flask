#!/usr/bin/env bash
import os
from flask import Flask, render_template ,request,send_file, send_from_directory,Response
from flask import jsonify
import cv2
from flask_cors import CORS
from flask_cors import cross_origin
import mysql.connector as sql
import subprocess
import threading
import io
from PIL import Image
from io import BytesIO
from io import StringIO ## for Python 3


# app = Flask(__name__)

app = Flask(__name__, static_folder='static')

DEFAULT_VIEW_MAP_LATITUDE = 39.74
DEFAULT_VIEW_MAP_LONGTITUDE = -104.99

host='localhost'
user = 'root'
password = 'root'
db = 'map'
con = sql.connect(host=host,user=user,password=password,db=db, use_unicode=True, charset='utf8') 
# con.autocommit(True)

folderdir = "video/24"
currentDirectory = os.getcwd()
cors = CORS(app, resources={r"/*": {"origins": "*"}})

liveObj = {}

# @app.route('/', methods=['GET'])
# def test():
#     return "Hello World !!"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/getframes', methods=['GET'])
@cross_origin()
def getFrames():
    try:
        frames = []
        for frame in os.listdir(currentDirectory+"/"+folderdir):
            obj = {}
            obj['file_path'] = frame
            frames.append(obj)
        return jsonify({"status":200,"data":frames})
    except:
        return jsonify({"status":500, "message" : "Something Went Wrong!!"})


# @app.route('/static/<imagename>',methods=['get'])
# @cross_origin()
# def sendImage(imagename):
#     fileName = currentDirectory+"/"+folderdir+"/"+imagename
#     return send_file(fileName)

@app.route('/getpoints', methods=['GET'])
@cross_origin()
def getPoints():
    try:
        points = []
        cursor = con.cursor()
        sql = "SELECT * FROM map_cameras WHERE is_active = %s"
        cursor.execute(sql, (1,))
        data = cursor.fetchall()
        print(data)
        for row in data:
            obj = {}
            obj['id'] = row[0]
            obj['name'] = row[1]
            obj['type'] = row[2]
            obj['address'] = row[3]
            obj['lat'] = row[4]
            obj['long'] = row[5]
            obj['is_active'] = row[6]
            obj['notes'] = row[7]
            points.append(obj)
        return jsonify({"status":200,"data":points, "lat":DEFAULT_VIEW_MAP_LATITUDE, "long":DEFAULT_VIEW_MAP_LONGTITUDE})
    except Exception as e:
        print(e)
        return jsonify({"status":500, "message" : "Something Went Wrong!!"})


@app.route('/getvideosbycamera', methods=['POST'])
@cross_origin()
def getVideosByCamera():
    try:
        print("API Called")
        reqData = request.get_json()
        queryDate = reqData['date'].split("T")[0]
        videos = []
        cursor = con.cursor()
        sql = "SELECT * FROM map_camera_videos WHERE camera_id = %s and video_date = %s"
        cursor.execute(sql, (reqData['camera_id'],queryDate,))
        print(reqData['camera_id'],queryDate)
        data = cursor.fetchall()
        con.commit()
        print("Query Called")
        print(videos)
        for row in data:
            print(row)
            obj = {}
            obj['id'] = row[0]
            obj['camera_id'] = row[1]
            obj['video_path'] = row[2]
            obj['thumbail_path'] = row[3]
            obj['video_duration'] = row[4]
            obj['video_name'] = row[5]
            obj['video_date'] = row[6]
            obj['start_time'] = row[7]
            obj['end_time'] = row[8]
            videos.append(obj)
        return jsonify({"status":200,"data":videos})
    except Exception as e:
        print(e)
        return jsonify({"status":500, "message" : "Something Went Wrong!!"})

@app.route('/videos/<cameraid>/<filename>',methods=['get'])
@cross_origin()
def viewRecordedVideo(cameraid,filename):
    # fileName = currentDirectory+"/1/2020-02-06 15:04:25.900493.mp4"
    fileName = "videos/"+cameraid+"/"+filename
    print(fileName)
    return send_file(fileName,as_attachment=False)
    
def recordVideos():
    cursor = con.cursor()
    sql = "SELECT * FROM map_cameras WHERE is_active = %s "
    cursor.execute(sql, (1,))
    data = cursor.fetchall()
    count = 0
    for row in data:
        count += 1
        if count < 3:
            if count == 1:
                cap = cv2.VideoCapture(0)
            else:
                cap = cv2.VideoCapture(2)
            command = ['python','./record.py','--cameraID',str(row[0])]
            process = subprocess.Popen(command)
            updateSubPID(row[0],process.pid)

def gen(cameraID):
    image_path = "videos/"+str(cameraID)+"/liveframe.jpg"
    while True:
        with open(image_path, 'rb') as f:
            check_chars = f.read()[-2:]
        if check_chars != b'\xff\xd9':
            pass
            # print('Not complete image')
        else:
            # imrgb = cv2.imread(os.path.join(path, file), 1)
            frame = cv2.imread(image_path)
            if frame is not None:
                image=frame.copy()
                ret,jpeg = cv2.imencode('.jpg',image)
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            else:
                pass


@app.route('/video_feed/<cameraID>',methods=['get'])
def viewLiveVideo(cameraID):
    # liveObj['id'] = cameraID
    # liveObj['flag'] = 0
    return Response(gen(cameraID),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/stoplive", methods=['post'])
@cross_origin()
def startStopFlag():
    try:
        capture.release()
        status={"status":200}
    except  Exception as e:
        status={"status":500,"result":str(e)}
    return jsonify(status)

def updateSubPID(cameraID,processID):
    try:
        cur = con.cursor()
        sql = "UPDATE map_cameras SET sub_id = %s where id = %s"
        val = (processID,cameraID)
        cur.execute(sql,val)
        con.commit()
    except:
        print("Update log error")

def apprun():
   app.run(host='0.0.0.0', port=3001)


if __name__ == '__main__':
    threading.Thread(target=apprun, args=()).start()
    threading.Thread(target=recordVideos, args=()).start()
    
