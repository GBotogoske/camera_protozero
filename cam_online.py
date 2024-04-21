#Import necessary libraries
from flask import Flask, render_template, Response
import cv2
#library to communicate with the operational system
import os
from datetime import datetime

#Initialize the Flask app
app = Flask(__name__)
camera_name= "Trust Webcam: Trust Webcam"


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
    cv2.imwrite("photo/" + get_data()+".jpg", put_date(frame))

    return "Picture taken!"  

cam_id=find_camera_id(camera_name)
camera = cv2.VideoCapture(-1,cv2.CAP_V4L)
font = cv2.FONT_HERSHEY_SIMPLEX

def main():
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    app.run(debug=False)

if __name__ == "__main__":
    main()
    