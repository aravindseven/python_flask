#!/usr/bin/env bash
import os
from flask import Flask, render_template ,request, send_from_directory,Response
from flask import jsonify
import cv2
import imagezmq

app = Flask(__name__)

image_hub = imagezmq.ImageHub()
print("Listening")
while True:  # show streamed images until Ctrl-C
    print("het")
    rpi_name, image = image_hub.recv_image()
    print(image)
    cv2.imshow(rpi_name, image) # 1 window for each RPi
    cv2.waitKey(1)
    image_hub.send_reply(b'OK')

@app.route('/', methods=['GET'])
def test():
    return "Hello World !!"

@app.route('/ipaccess',methods=['get'])
def sendVideoStream():
    print("Send Stream")
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen():
    image_hub = imagezmq.ImageHub()
    while True:
        rpi_name, image = image_hub.recv_image()
        print(rpi_name)
        # cv2.imshow(rpi_name, image) 
        # cv2.waitKey(1)
        image_hub.send_reply(b'OK')
        ret,jpeg = cv2.imencode('.jpg',image)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        
# def check():
#     while True:  # show streamed images until Ctrl-C
#         print("het")
#         rpi_name, image = image_hub.recv_image()
#         print(image)
#         cv2.imshow(rpi_name, image) # 1 window for each RPi
#         cv2.waitKey(1)
#         image_hub.send_reply(b'OK')

# if __name__ == '__main__':
#     check()
#     app.run(host='0.0.0.0', port=3001)
    
