#!/usr/bin/env bash
import os
from flask import Flask, render_template ,request, send_from_directory
from flask import jsonify
from facecompare.demos.face_compare import *
from demographic.main.demographic import *
from gender.gender import *
import pickle
import time
import boto3
from botocore.client import Config
import listendir
import threading 
from datetime import datetime
import mysql.connector as sql

app = Flask(__name__)

pickleFolder = "./pickle"
pickleFolderImgRef = "./pickle_img_ref"
pickle_file_names = []
face_encodings = []
count = 0
face_comparision_threshold = 0.47
reg_id = 0

host='localhost'
user = 'root'
password = 'root'
db = 'aiverify'
con = sql.connect(host=host,user=user,password=password,db=db, use_unicode=True, charset='utf8') 

# Load the pickle file encodings and names to a list
def Load_pickle():
    if len(os.listdir(pickleFolder)) != 0:
        for filename in sorted(os.listdir(pickleFolder)):
            pickle_file_names.append(filename)
            open_pickle = pickle.load(open(pickleFolder + '/' + filename, "rb"))
            face_encodings.append(open_pickle)
#function call Load_pickle        
Load_pickle()

@app.route('/', methods=['GET'])
def test():
    return "Hello World !!"

@app.route('/defaultthreshold', methods=['GET'])
def defaultThreshold():
    return jsonify({"status":200, "threshold" : face_comparision_threshold})
    

# API for registration     
@app.route('/registration', methods=['POST'])
def register():
    start = time.time()
    # Request license and selfie as input
    try:
        data = request.form['threshold']
        if float(request.form['threshold']) > 0:
            threshold = float(request.form['threshold'])
        else:
            threshold = face_comparision_threshold
        selfie = request.files['selfie'].read()
        proof = request.files['proof'].read()
        if int(request.form['retry']) == 0:
            folderName = saveRequestData(selfie,proof)
        
        print(threshold)
        s3time = time.time() - start
    except KeyError as e:
        return jsonify ({"status" : 400, "message": "Use Input key as selfie/proof or input image for registration", "exception":str(e)})
    fstart = time.time()
    faceCompare_score = facecompare(selfie,proof)
    facecomparisionTime = time.time() - fstart
    status = faceCompare_score['status']
    if int(request.form['retry']) == 0:
        print("New Record")
        saveLog = insertLog(folderName,threshold)
    else:
        print("not new record")
        saveLog = int(request.form['id'])
    if status == 200:
        print("score")
        print(float(faceCompare_score['score']))
        if float(faceCompare_score['score']) < threshold:
            #Faces matched (selfie with proof)
            #Before going to extract the demographic check the user is already registered
            estart = time.time()
            user_excists = checkWithExcistingUsers(faceCompare_score['s_rep'],faceCompare_score['s_image'])
            execistinguserTime = time.time() - estart
            # 1 user not excists 
            if user_excists == 1:
                #Extract Demographics from the proof image
                dstart = time.time()
                demographics = demographic(faceCompare_score['p_image'])
                print(demographics)
                status = demographics['status']
                if status != 200:
                    return jsonify(demographics) 
                demographicTime = time.time() - dstart
                if demographics['gender'] == 0:
                    # Not able to identify the gender from DL.Load gender model and identify using the DL cropped face
                    start = time.time()
                    gender = detect_gender(faceCompare_score['p_c_image'])
                    genderTime = time.time() - start
                    print("Gender total time took {} seconds.".format(time.time() - start))
                    if gender is not None:
                        demographics['gender'] = gender

                demographics['face_matched'] =True
                demographics['user_id'] = reg_id
                demographics['face_time'] = facecomparisionTime
                demographics['user_time'] = execistinguserTime
                demographics['demographic_time'] = demographicTime
                demographics['gender_time'] = genderTime
                demographics['s3time'] = s3time
                demographics['id'] = saveLog
                return jsonify(demographics)
            else:
                user_excists['id'] = saveLog
                return jsonify(user_excists)
        else:
            print("Faces not matched")
            updateThresholdLog(saveLog,threshold)
            return jsonify({"status":500,"id":saveLog, "message" : "Faces not matched","face_matched" : False})
    else:
        faceCompare_score['id'] = saveLog
        return jsonify(faceCompare_score)

# Verify Face
@app.route('/inference', methods=['POST'])
def inference():
    try:
        selfie = request.files['selfie'].read()
        user_id = request.form.get('user_id')
    except KeyError as e:
        return jsonify ({"status" : 400, "message": "Use Input key as selfie/user_id or input image for registration", "exception":str(e)})
    
    #get excisting face rep based on userid
    try:
        userIndex = pickle_file_names.index(user_id+".pkl")
        print(userIndex)
    except:
        return jsonify ({"status" : 500, "message": "User id not found"})            

    selfie_rep = getFaceRep(selfie)
    status = selfie_rep['status']
    if status != 200:
        return jsonify(selfie_rep)
    else:
        # Got verify face selfie face representation
        verify_rep = selfie_rep['rep']
        pickle_rep = face_encodings[userIndex]
        if pickle_rep is None:
            return jsonify ({"status" : 500, "message": "User id not found"})
        else:
            faceDistance = faceDistanceScore(verify_rep,pickle_rep)
            if float(faceDistance) < face_comparision_threshold:
                return jsonify({"status":200, "message" : "Faces matched","face_matched" : True})
            else:
                return jsonify({"status":500, "message" : "Faces not matched","face_matched" : False})

@app.route('/updatelog', methods=['POST'])
def updateLog():
    try:
        cur = con.cursor()
        sql = "UPDATE dataset_log SET threshold = %s,is_same_user = %s , status = %s where id = %s"
        val = (request.form.get('threshold'),request.form.get('is_same_user'),request.form.get('status'),int(request.form.get('id')))
        cur.execute(sql,val)
        con.commit()
        return jsonify({"status":200,"message":"Updated Successfully"})
    except:
        return jsonify({"status":500, "message" : "Something Went Wrong!!"})

def updateThresholdLog(id,threshold):
    try:
        cur = con.cursor()
        sql = "UPDATE dataset_log SET threshold = %s where id = %s"
        val = (threshold,id)
        cur.execute(sql,val)
        con.commit()
    except:
        print("Update log error")

def saveRequestData(selfie,proof):
    # millis = int(round(time.time() * 1000))
    millis = datetime.now()
    if not os.path.exists("request_data/"+str(millis)):
        os.makedirs("request_data/"+str(millis))
    
    npimg = np.fromstring(selfie, np.uint8)
    selfie = cv2.imdecode(npimg, 1)
    cv2.imwrite("request_data/"+str(millis)+'/selfie.jpg',selfie)

    npimg = np.fromstring(proof, np.uint8)
    proof = cv2.imdecode(npimg, 1)
    cv2.imwrite("request_data/"+str(millis)+'/proof.jpg',proof)
    return millis

def insertLog(folderName,threshold):
    cur = con.cursor()
    cur.execute("INSERT INTO dataset_log (folder_name,threshold) VALUES('%s','%s')"%(folderName,threshold))
    con.commit()
    id = cur.lastrowid
    return id

def checkWithExcistingUsers(source_rep,s_image):
    user_id = len(face_encodings) + 1
    for idx, f in enumerate(face_encodings):
        faceDistance = faceDistanceScore(source_rep,f)
        # if float(faceDistance) < face_comparision_threshold:
        #     return {"status": 204, "message": "This person is already registered as user ID : "  +  pickle_file_names[idx].split(".")[0]}
            
    #save the new user rep into pickle file
    data = source_rep
    global reg_id
    reg_id = user_id
    name =  str(user_id) + ".pkl"
    f = open(pickleFolder + '/' + str(user_id) +".pkl", "wb")
    f.write(pickle.dumps(data))
    f.close()

    if not os.path.exists(pickleFolderImgRef+"/"+str(user_id)):
            os.mkdir(pickleFolderImgRef+"/"+str(user_id))

    cv2.imwrite(pickleFolderImgRef+"/"+str(user_id)+'/selfie.jpg',s_image)
    face_encodings.append(source_rep)
    pickle_file_names.append(str(user_id) + ".pkl")
    return 1

def apprun():
   app.run(host='0.0.0.0', port=5002)

def lister():
    listendir.main()

if __name__ == '__main__':
    threading.Thread(target=apprun, args=()).start()
    threading.Thread(target=lister, args=()).start()
    