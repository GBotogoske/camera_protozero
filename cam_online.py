#Import necessary libraries

#library for  web interface applications
from flask import Flask, render_template, Response, send_file, send_from_directory
#library for camera applications
import cv2
import typing as _typing
#library to communicate with the operational system
import os
#Library to get date
from datetime import datetime
#library to handle threads 
import threading
#library for wait functions
import time

import numpy as np



#Initialize the Flask app
app = Flask(__name__)
#camera name, check the name of your camera at /sys/class/video4linux/video(i)/name (OBRIGADO) 
camera_name= "Trust Webcam: Trust Webcam"
res_x=1280
res_y=720
font = cv2.FONT_HERSHEY_SIMPLEX #font to the date text

#to the video recording
mutex = threading.Lock()

#return the date in the format DDMMYYYYHHMMSS
def get_data():
    now=datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    return dt_string

#return the date in the format DD/MM/YYYY-HH:MM:SS
def get_beauty_date():
    now=datetime.now()
    dt_string = now.strftime("%d/%m/%Y-%H:%M:%S")
    return dt_string

#function that seatch the id of the camera by the given name
def find_camera_id(camera_name):
    devices_path = "/sys/class/video4linux"
    if not os.path.exists(devices_path):
        print("No video4linux devices found")
        return
    i=0
    for device in sorted(os.listdir(devices_path)):
        device_path = os.path.join(devices_path, device)
        if os.path.isdir(device_path):
            try:
                name_file = os.path.join(device_path, "name")
                with open(name_file, "r") as f:
                    name = f.readline().strip()
                    if name == camera_name:
                        break
                    
            except IOError:
                pass  # Skip if unable to read
            i=i+1
    return i

#function that put date in the frame
def put_date(frame):
    return cv2.putText(frame, get_beauty_date(),(10, 100),font, 1, (255,255,255))

def generate_black():
    img = np.zeros((res_y, res_x, 3), dtype = np.uint8)
    img=cv2.putText(img, "NO DATA",(50, 50),font, 1, (255,255,255))
    return img

img_black = generate_black()

success: bool
frame = None
frame_date = None
#function that generate frame from time to time
def gen_frames(): 
    global success
    global frame, frame_date 
    while True:
        if camera.isOpened():
            success, frame = camera.read()  # read the camera frame
            if not success:
                frame=img_black
        else:
            frame=img_black
            success=False
        frame_date = put_date(frame)   
        ret, buffer = cv2.imencode('.jpg', frame_date)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result
        time.sleep(0)
        
#start function that creates the web interface defined at index.html            
@app.route('/')
def index():
    return render_template('index.html')

#function thart return the real time video to the web interface
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

#function that takes picture
@app.route('/take_picture')
def take_picture():
    
    print("Taking picture...")
    #ret, frame = camera.read()
    name=get_data()+".jpg"
    cv2.imwrite("photo/" + name , frame_date)

    return send_from_directory("photo/" , name, as_attachment=True)


is_recording=False
fps=24.0
n_frames=0

#theread for recording the video
video_file_name = None
def recording(mutex):
    global n_frames
    global video_file_name
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_file = cv2.VideoWriter()
    with mutex:
        video_file_name=get_data()+".avi"
        video_file = cv2.VideoWriter("video/"+video_file_name, fourcc, fps, (res_x,res_y))
        global is_recording 
        is_recording= True
        print("Starting video...")
        while is_recording == True:
            #if camera.isOpened():
                #ret, frame = camera.read()
                #if success==True:
            time.sleep(1.0/fps)                
            video_file.write(frame_date)
            
        video_file.release()
        print("Ending video")

#function that start the video recording
recording_thread = None
@app.route('/start_video')
def start_video():
    global recording_thread
    recording_thread = threading.Thread(target=recording, args=(mutex,))
    recording_thread.start() #create a thread to record the video       
    return "True"

#function that stop the video recording
@app.route('/stop_video')
def stop_video():
    global is_recording
    is_recording=False
    recording_thread.join()
    print("sending video: " + video_file_name)
    return send_from_directory("video/" , video_file_name , as_attachment=True)


@app.route('/reset_camera')
def reset_camera():
    print("reseting camera")
    global cam_id
    cam_id=find_camera_id(camera_name) #find the id of camera based on his name on the linux interface
    global camera
    global success 
    camera.release()
    
    time.sleep(1)
    camera = cv2.VideoCapture(cam_id,cv2.CAP_V4L) #variable that reads the camera
    if not camera.isOpened():
        print("Error: Could not open camera.")
        success=False
    else:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, res_x)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, res_y)
    return "True"

cam_id=find_camera_id(camera_name) #find the id of camera based on his name on the linux interface


def main(): #this is the main thread
    global success
    global camera
    camera = cv2.VideoCapture(cam_id,cv2.CAP_V4L) #variable that reads the camera
    if not camera.isOpened():
        print("Error: Could not open camera.")
        success=False
    else:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, res_x)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, res_y)
    try:
        os.mkdir("photo")
    except:
        print("photo dir already exists")
    try:
        os.mkdir("video")
    except:
        print("video dir already exists")
    app.run(debug=False)


if __name__ == "__main__":
    main_thread = threading.Thread(target=main)  #create main theread than handles the web interface
    main_thread.start() # start the main thread
    
    
    