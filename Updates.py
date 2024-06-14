from djitellopy import tello
import TestKeyboard as kp
from time import sleep
import cv2
import numpy as np
from pygame import mixer
import time

import threading  # Import the threading module for concurrent operations
from djitellopy import tello  # Import the Tello library for drone interaction
import cv2  # Import OpenCV for video frame operations

#######################  NEW - 2 ############################
# Declare a threading Event to signal readiness of video streaming
# Best practice for complex applications: encapsulate shared resources in a class
stream_ready = threading.Event()
##########################################################
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
        cv2.imwrite(rf'C:\Users\ocard\Desktop\test_field\ParkerDrone2.0\FlightFoto{time.time()}.jpg',cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        return img, [myFaceListC[i],myFaceListArea[i]]
    else:
        return img, [[0,0],0]

def trackFace(me,info,w,pid,pError):
    fbRange = [6200,6800]
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
def getKeyboardInput(drone):
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

    if kp.getKey("q"):  drone.land()
    if kp.getKey("e"): drone.takeoff()

    if kp.getKey("x"): print(drone.get_battery())
    return [lr,fb,ud,yv]

def flight_routine(drone,pError, pid,w,h):
    #######################  NEW - 4 ############################
    print("waiting for event to signal video stream readiness")

    # Wait for the event signaling video stream readiness
    stream_ready.wait()

    print("event signaled for video stream readiness")
    ##########################################################

    # Send the takeoff command, movement commands, and lastly, the land command
    while True:
        vals = getKeyboardInput(drone)
        drone.send_rc_control(vals[0],vals[1],vals[2],vals[3])
        img = drone.get_frame_read().frame
        img, info = findFace(img)
        pError = trackFace(drone,info,w,pid,pError)
        print("Area",info[1],"Center",info[0])

def stream_video(drone):
    while True:
        frame = drone.get_frame_read().frame
        # Check if frame reading was successful
        cv2.imshow('tello stream', cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        #######################  NEW - 3 ############################
        # Check if streaming readiness hasn't been signaled yet
        if not stream_ready.is_set():

            # Signal that video streaming is ready
            stream_ready.set()
            print("Event Signal Set: Stream is live.")
        ##########################################################

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

def main():
    # Initialize the drone, connect to it, and turn its video stream on.
    kp.init()
    global img
    w,h = 360,200
    pid=[0.4,0.4,0]
    pError = 0
    drone = tello.Tello()
    drone.connect()
    drone.streamon()
    print(f'Drone Battery: {drone.get_battery()}%')
    print("drone connected and stream on. Starting video stream thread.\n")

    #######################  NEW - 1 ############################
    # Create and start the streaming thread
    stream_thread = threading.Thread(target=stream_video, args=(drone,))

    # Set thread as a daemon thread to have it run in the background.
    # This allows our program to exit even if this streaming thread is still running after calling drone.reboot()
    # Also, this prevents errors in our video stream function from crashing our entire program if they occur.
    stream_thread.daemon = True

    # Start the thread
    stream_thread.start()
    ##########################################################

    # Execute the flight routine
    flight_routine(drone,pError, pid,w,h)

    print("Flight routine ended. Rebooting drone now...")

    # Reboot the drone at the end
    drone.reboot()


if __name__ == "__main__":
    # Run the main function if this script is executed
    main()