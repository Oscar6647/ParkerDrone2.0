from djitellopy import tello
import TestKeyboard as kp
from time import sleep
import cv2

import threading  # Import the threading module for concurrent operations
from djitellopy import tello  # Import the Tello library for drone interaction
import cv2  # Import OpenCV for video frame operations

#######################  NEW - 2 ############################
# Declare a threading Event to signal readiness of video streaming
# Best practice for complex applications: encapsulate shared resources in a class
stream_ready = threading.Event()
##########################################################

def flight_routine(drone):
    #######################  NEW - 4 ############################
    print("waiting for event to signal video stream readiness")

    # Wait for the event signaling video stream readiness
    stream_ready.wait()

    print("event signaled for video stream readiness")
    ##########################################################

    # Send the takeoff command, movement commands, and lastly, the land command
    print("takeoff\n")
    drone.takeoff()
    v_up = 0
    for _ in range(16):
                drone.send_rc_control(10, -1, v_up, -13)
                sleep(4)
                drone.send_rc_control(0,0,0,0)
                sleep(0.5)
    drone.land()

def stream_video(drone):
    while True:
        frame = drone.get_frame_read().frame
        # Check if frame reading was successful
        cv2.imshow('tello stream', frame)

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
    fbRange = [6200,6800]
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
    flight_routine(drone)

    print("Flight routine ended. Rebooting drone now...")

    # Reboot the drone at the end
    drone.reboot()


if __name__ == "__main__":
    # Run the main function if this script is executed
    main()