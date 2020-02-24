import numpy as np
import cv2
import time
from time import time
import threading
import datetime
import mysql.connector as sql
import os
import subprocess

print("Started")
# FNULL = open(os.devnull,'w')
command = ['python','/home/nuc-obs-06/projects/Aravind_trevor/study/map/map_server/subprocesscheck.py']
process = subprocess.Popen(command)
print(process.pid)