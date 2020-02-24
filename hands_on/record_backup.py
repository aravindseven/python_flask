import numpy as np
import cv2
import time
from time import time
import threading
import datetime
import mysql.connector as sql
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--cameraaddress', help='foo help',default="1")
parser.add_argument('--cap', help='foo help',default="1")
parser.add_argument('--cursor', help='foo help',default="1")
parser.add_argument('--cameraID', help='foo help',default="1")

args = parser.parse_args()

def videoRecord(args.cap,cameraID,cursor):

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    currentDate = datetime.datetime.now()
    video_name = currentDate
    video_date = datetime.datetime.strftime(currentDate, '%Y-%m-%d')
    print("Current Date ", currentDate)
    print("Video Date ", video_date)
    start = datetime.datetime.strftime(currentDate, '%I:%M %p')
    print("Start Time", start)
    video_path = str(cameraID)+'/'+str(video_name)+'.avi'
    if not os.path.exists(str(cameraID)):
        os.makedirs(str(cameraID))
    out = cv2.VideoWriter(str(cameraID)+'/'+str(video_name)+'.avi',fourcc, 20.0, (640,480))
    print("####################")
    start_time = time()
    print(start_time)
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret==True:
            frame = cv2.flip(frame,0)
            # write the flipped frame
            out.write(frame)

            end_time = time()
            seconds_elapsed = end_time - start_time
            hours, rest = divmod(seconds_elapsed, 3600)
            minutes, seconds = divmod(rest, 60)
            # print(int(minutes))
            if int(minutes) > 2:
                print(int(minutes))
                end = datetime.datetime.strftime(currentDate, '%I:%M %p')
                print("End Time", end)
                # print("More than 15 minutes", cameraID)
            # cv2.imshow('frame',frame)
            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break
        else:
            break
    else:
        print("Camera is not Opened")
        break

    # Release everything if job is finished
    print("Finished")
    
    

    
    print(hours,minutes,seconds)
    cap.release()
    out.release()
    cv2.destroyAllWindows()

if __name__ == "__main__": 
    cursor = con.cursor()
    cap = cv2.VideoCapture(0)
    cap1 = cv2.VideoCapture(2)
    t1 = threading.Thread(target=videoRecord, args=(cap,0,cursor)) 
    
    t2 = threading.Thread(target=videoRecord, args=(cap1,2,cursor)) 
  
    # starting thread 1 
    t1.start() 
    # starting thread 2 
    t2.start() 
    
    print("My Job Done Bye")