import numpy as np
import cv2
import time
from time import time
import threading
import datetime
import mysql.connector as sql
import os

print("AAAAAAAAAAA")
cap = cv2.VideoCapture(0)

while(cap.isOpened()):
    ret, frame = cap.read()
    if ret==True:
        frame = cv2.flip(frame,0)
        # print(frame)
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("inside")
            break
    else:
        break
else:
    print("Camera is not Opened")


# Release everything if job is finished
print("Finished")
