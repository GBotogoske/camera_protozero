#Import necessary libraries
from flask import Flask, render_template, Response, send_file, send_from_directory
import cv2
#library to communicate with the operational system
import os
from datetime import datetime
import threading
import time

#Initialize the Flask app
app = Flask(__name__)
camera_name= "Trust Webcam: Trust Webcam"

#to the video recording
mutex = threading.Lock()

def get_data():
    now=datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    return dt_string

def get_beauty_date():
    now=datetime.now()
    dt_string = now.strftime("%d/%m/%Y-%H:%M:%S")
    return dt_string

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

def put_date(frame):
    return cv2.putText(frame, get_beauty_date(),(10, 100),font, 1, (255,255,255))

def gen_frames():  
    while True:
        success, frame = camera.read()  # read the camera frame
        frame = put_date(frame)
        if not success:
            break
        else:

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
            #time.sleep(1.0/fps)
        
            
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/take_picture')
def take_picture():
    
    print("Taking picture...")
    ret, frame = camera.read()
    name=get_data()+".jpg"
    cv2.imwrite("photo/" + name , put_date(frame))

    return send_from_directory("photo/" , name, as_attachment=True) 

fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_file = cv2.VideoWriter()
is_recording=False
fps=24.0
n_frames=0
def recording(mutex):
    global n_frames
    with mutex:
        video_file = cv2.VideoWriter("video/"+get_data()+".avi", fourcc, fps, (1280,720))
        global is_recording 
        is_recording= True
        print("Starting video...")
        while is_recording == True:
            if camera.isOpened():
                ret, frame = camera.read()
                if ret==True:
                    video_file.write(cv2.putText(frame, get_beauty_date(),(10, 100),font, 1, (255,255,255)))
            #n_frames=n_frames+1        
            #print(n_frames)        
            #print(1/fps)
            #time.sleep(1.0/fps)

        video_file.release()
        print("Ending video")


@app.route('/start_video')
def start_video():
    
    #fourcc = cv2.VideoWriter_fourcc(*'XVID')
    #out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640,480))
    recording_thread = threading.Thread(target=recording, args=(mutex,))
    recording_thread.start()
        
    return "True"

@app.route('/stop_video')
def stop_video():
    global is_recording
    is_recording=False
    return "True"

cam_id=find_camera_id(camera_name)
#camera = cv2.VideoCapture(camera_name,cv2.CAP_V4L)
camera = cv2.VideoCapture(-1,cv2.CAP_V4L)
font = cv2.FONT_HERSHEY_SIMPLEX

def main():
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
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
    main_thread = threading.Thread(target=main)
    main_thread.start()
    
    
    