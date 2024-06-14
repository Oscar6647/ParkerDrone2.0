from djitellopy import tello
from threading import Thread
from pygame import mixer
import TestKeyboard as kp
import numpy as np
import time
import cv2
import os

kp.init()
mixer.init()
me = tello.Tello()
me.connect()
print(me.get_battery())
global img
me.streamon()

w,h = 360,200
fbRange = [6200,6800]
pid=[0.4,0.4,0]
pError = 0

def findFace(img):
    faceCascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(imgGray, 1.2,8)

    myFaceListC = []
    myFaceListArea = []

    for(x,y,w,h) in faces:
        mixer.music.load("SNAP.mp3")
        # Setting the volume
        mixer.music.set_volume(0.7)
  
        # Start playing the song
        mixer.music.play()
        #cv2.rectangle(img,(x,y),(x+w,y+h),(0,0,255),2)
        cx = x+w //2
        cy = y+h //2
        area = w*h
        #cv2.circle(img,(cx,cy),5,(0,255,0),cv2.FILLED)
        myFaceListC.append([cx,cy])
        myFaceListArea.append(area)
    if len(myFaceListArea) != 0:
        i = myFaceListArea.index(max(myFaceListArea))
        cv2.imwrite(f'C:/Users/OCG/Desktop/NAVY/Foto Flight{time.time()}.jpg',img)
        return img, [myFaceListC[i],myFaceListArea[i]]
    else:
        return img, [[0,0],0]

def trackFace(me,info,w,pid,pError):
    area = info[1]
    x,y = info[0]
    fb = 0

    error = x-w//2
    speed = pid[0]*error +pid[1]*(error-pError)
    speed = int(np.clip(speed,-100,100))
    
    if area > fbRange[0] and area <fbRange[1]:
        fb = 0
    elif area >fbRange[1]:
        fb =-20
    elif area <fbRange[0] and area != 0:
        fb = 20

    if x == 0:
        speed = 0
        error = 0

    me.send_rc_control(0,fb,0,speed)
    return error
    

def getKeyboardInput():
    lr,fb,ud,yv = 0,0,0,0
    speed = 50
    if kp.getKey("LEFT"):  lr = -speed
    elif kp.getKey("RIGHT"): lr = speed

    if kp.getKey("UP"):  fb = speed
    elif kp.getKey("DOWN"): fb = -speed

    if kp.getKey("w"):  ud = speed
    elif kp.getKey("s"): ud = -speed

    if kp.getKey("a"):  yv = speed
    elif kp.getKey("d"): yv = -speed

    if kp.getKey("q"):  me.land()
    if kp.getKey("e"): me.takeoff()

    if kp.getKey("x"): print(me.get_battery())
    return [lr,fb,ud,yv]


while True:
    vals = getKeyboardInput()
    me.send_rc_control(vals[0],vals[1],vals[2],vals[3])
    img = me.get_frame_read().frame
    img, info = findFace(img)
    pError = trackFace(me,info,w,pid,pError)
    print("Area",info[1],"Center",info[0])
    cv2.imshow("Image",img)
    cv2.waitKey(1) 

