import numpy as np
import cv2
import time
from time import time
import threading
import datetime
import mysql.connector as sql
import os
import argparse
import subprocess
import signal

parser = argparse.ArgumentParser()
parser.add_argument('--cameraID', help='foo help',default="1")

args = parser.parse_args()

host='localhost'
user = 'root'
password = 'root'
db = 'map'
con = sql.connect(host=host,user=user,password=password,db=db, use_unicode=True, charset='utf8') 
start_time = time()
def videoRecord(cap,cameraID,cursor,cameraobj):

    # Define the codec and create VideoWriter object
    # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    # fourcc = cv2.VideoWriter_fourcc(*'H264')
    # fourcc = 0x00000021
    fourcc = cv2.VideoWriter_fourcc(*'vp80')
    currentDate = datetime.datetime.now()
    video_name = currentDate
    video_date = datetime.datetime.strftime(currentDate, '%Y-%m-%d')
    start = datetime.datetime.strftime(currentDate, '%I:%M %p')
    video_path = "videos/"+str(cameraID)+'/'+str(video_name)+'.webm'
    thumbail_path = "videos/"+str(cameraID)+'/liveframe.jpg'
    if not os.path.exists("videos/"+str(cameraID)):
        os.makedirs("videos/"+str(cameraID))
    out = cv2.VideoWriter("videos/"+str(cameraID)+'/'+str(video_name)+'.webm',fourcc, 20.0, (640,480))
    global start_time
    start_time = time()
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret==True:
            cv2.imwrite(thumbail_path,frame)
            out.write(frame)

            end_time = time()
            seconds_elapsed = end_time - start_time
            hours, rest = divmod(seconds_elapsed, 3600)
            minutes, seconds = divmod(rest, 60)
            if minutes > 4.0:
                end = datetime.datetime.strftime(datetime.datetime.now(), '%I:%M %p')
                #save video path in db
                saveVideoDetails(cameraID,video_path,video_name,video_date,start,end)
                #get process id of the camera and kill it
                cursor = con.cursor()
                sql = "SELECT * FROM map_cameras WHERE is_active = %s and id = %s"
                cursor.execute(sql, (1,args.cameraID,))
                data = cursor.fetchall()
                cameraobj = {}
                for row in data:
                    if row[9] is not None:
                        #create new sub process and kill the old sub process
                        createDestroySubProcess(row[9])
        else:
            #same have to handle
            break
    else:
        print("Camera is not Opened")
        #have to handle if camera not opended

    # Release everything if job is finished
    # print("Finished")
    cap.release()
    out.release()
    cv2.destroyAllWindows()

def createDestroySubProcess(processID):
    #destroy the 
    command = ['python','./record.py','--cameraID',str(args.cameraID)]
    process = subprocess.Popen(command)
    updateSubPID(args.cameraID,process.pid)
    os.kill(int(processID), signal.SIGTERM)
    

def updateSubPID(cameraID,processID):
    try:
        cur = con.cursor()
        sql = "UPDATE map_cameras SET sub_id = %s where id = %s"
        val = (processID,cameraID)
        cur.execute(sql,val)
        con.commit()
    except:
        print("Update log error")

def saveVideoDetails(cameraID,video_path,video_name,video_date,start,end):
    try:
        cur = con.cursor()
        sql = "INSERT into map_camera_videos (camera_id,video_path,thumbail_path,video_duration,video_name,video_date,start_time,end_time) values ('%s','%s','%s','%s','%s','%s','%s','%s')"%(cameraID,video_path,"thumbail","2",video_name,video_date,start,end)
        cur.execute(sql)
        con.commit()
    except:
        print("Insert log error")


if __name__ == "__main__": 
    cursor = con.cursor()
    sql = "SELECT * FROM map_cameras WHERE is_active = %s and id = %s"
    cursor.execute(sql, (1,args.cameraID,))
    data = cursor.fetchall()
    cameraobj = {}
    for row in data:
        cameraobj['id'] = row[0]
        cameraobj['name'] = row[1]
        cameraobj['type'] = row[2]
        cameraobj['address'] = row[3]
        cameraobj['lat'] = row[4]
        cameraobj['long'] = row[5]
        break
    if args.cameraID == "1":
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(2)
    videoRecord(cap,args.cameraID,cursor,cameraobj)

    
    