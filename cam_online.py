#Import necessary libraries

#library for  web interface applications
from flask import Flask, render_template, Response, request, send_from_directory, jsonify
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
#library numpy
import numpy as np

from functions.useful_function import get_default_folder

#Initialize the Flask app
app = Flask(__name__)
#camera name, check the name of your camera at /sys/class/video4linux/video(i)/name (OBRIGADO) 
camera_name= "HD USB Camera"
res_x=1280
res_y=720
font = cv2.FONT_HERSHEY_SIMPLEX #font to the date text
PHOTO_DIR = "/photo"
VIDEO_DIR = "/video"
DEFAULT_DIR = get_default_folder()
HOME_DIR = DEFAULT_DIR

#to the video recording
mutex = threading.Lock()
mutex_photo = threading.Lock()

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
        # Define the text properties
    text = get_beauty_date()
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_thickness = 2 # Thickness of the border
    font_color =  (255,255,255)
    border_color = (0,0,0) 

    # Get the size of the text
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)

    # Calculate the position to put the text
    text_x = 0
    text_y = 30

    # Draw the border text
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, border_color, thickness=font_thickness+4)

    # Draw the actual text
    cv2.putText(frame, text, (text_x, text_y), font, font_scale, font_color, thickness=font_thickness)

    return frame

#create black image when camera is not connected
def generate_black():
    #global img_black
    img_black = np.zeros((res_y, res_x, 3), dtype = np.uint8)

    img_=cv2.putText(img_black, "NO DATA",(int(res_x/2), int(res_y/2)),font, 1, (255,255,255))
    time.sleep(0.1)
    return img_


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
                frame=generate_black()
        else:
            frame=generate_black()
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

#function that return the real time video to the web interface
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

#function that takes picture
@app.route('/take_picture')
def take_picture():
    
    print("Taking picture...")
    #ret, frame = camera.read()
    name=get_data()+".jpg"
    cv2.imwrite(HOME_DIR+PHOTO_DIR+"/" + name , frame_date)

    return send_from_directory(HOME_DIR+PHOTO_DIR+"/" , name, as_attachment=True)

now_time =0
#thread that handles the temporized photos
def photo_thread(mutex_photo):
    global now_time
    now_time = 0
    global is_taking_photo
    with mutex_photo:
        while now_time <= timer_total and is_taking_photo:
            print("Taking temporized pictures...")
            #ret, frame = camera.read()
            name=get_data()+".jpg"
            cv2.imwrite(HOME_DIR+PHOTO_DIR+"/" + name , frame_date)
            now_time=now_time+timer_interval
            print(now_time)
            time.sleep(timer_interval)
    is_taking_photo=False
    print("stoping pictures")

#function for the temporized photos    
timer_total=10
timer_interval=1
photo_thread_var=None
is_taking_photo = False
@app.route('/tp_function',methods=['POST'])
def tp_function():
    global timer_total
    global timer_interval
    global photo_thread_var
    global is_taking_photo
    data = request.json
    text_total = data.get('text')
    text_interval = data.get('text_i')
    print(text_interval)
    print(text_total)
    try:
        timer_total = float(text_total)  # Convert the string to a floating-point number
    except ValueError:
        timer_total = 10 # Return 10 if the string is not a valid number

    try:
        timer_interval = float(text_interval)  # Convert the string to a floating-point number
    except ValueError:
        timer_interval = 1 # Return 10 if the string is not a valid number
    
    if not is_taking_photo:
        is_taking_photo=True
        # Process the text here (you can modify parameters or perform any other action)
        print("timer interval")
        print(timer_interval)
        print("timer total")
        print(timer_total)
        photo_thread_var = threading.Thread(target=photo_thread, args=(mutex_photo,))
        photo_thread_var.start() #create a thread to record the photo 
    else:
        is_taking_photo=False   
    return "True"


#function that handles the status of actual homefolder
@app.route('/homefolder_status')
def homefolder_status():
    def generate():
        # Send messages periodically
        while True:
           # print("Temp\n" + str(500))
            yield "data: {}\n\n".format("Folder: " + HOME_DIR)
            time.sleep(5)  # Send status every 5 second
            #time.sleep(1)  # Simulate delay
    return Response(generate(), mimetype='text/event-stream')

#function that handles the status of picture timer
@app.route('/photo_status')
def photo_status():
    def generate():
        global is_taking_photo
        global timer_total
        global timer_interval
        # Send messages periodically
        while True:
           # print("Temp\n" + str(500))
            yield "data: {}\n\n".format("Temporized photos: ON -- Total time: {}s -- Interval: {}s".format(timer_total, timer_interval) if is_taking_photo else "Temporized Photos OFF")
            time.sleep(1)  # Send status every 1 second
            #time.sleep(1)  # Simulate delay
    return Response(generate(), mimetype='text/event-stream')

#function that handles the status of video
@app.route('/video_status')
def video_status():
    def generate_video():
        global is_recording
        global default_video_time
        global fps
        global n_frames
        # Send messages periodically
        while True:
            time_recording=n_frames/fps
           # print("Temp\n" + str(500))
            yield "data: {}\n\n".format("VIDEO RECORDING ON -- Total time: {}s -- Now time: {}s".format(default_video_time, time_recording) if is_recording else "VIDEO RECORDING OFF")
            time.sleep(1)  # Send status every 1 second
            #time.sleep(1)  # Simulate delay
    return Response(generate_video(), mimetype='text/event-stream')


is_recording=False
fps=24.0
#theread for recording the video
video_file_name = None
def recording(mutex):
    global n_frames
    global video_file_name
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_file = cv2.VideoWriter()
    with mutex:
        video_file_name=get_data()+".avi"
        video_file = cv2.VideoWriter(HOME_DIR+VIDEO_DIR+"/"+video_file_name, fourcc, fps, (res_x,res_y))
        global is_recording 
        is_recording= True
        print("Starting video...")
        while is_recording == True:
            #if camera.isOpened():
                #ret, frame = camera.read()
                #if success==True:
            n_frames=n_frames+1
            time.sleep(1.0/fps)                
            video_file.write(frame_date)
            
        video_file.release()
        n_frames=0
        print("Ending video")

n_frames=0
#thread for recording temporized videos
def recording_time(mutex):
    global n_frames
    n_frames=0
    max_time=60 #seconds
    n_frames_max=0
    global video_file_name
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video_file = cv2.VideoWriter()
    with mutex:
        video_file_name=get_data()+".avi"
        video_file = cv2.VideoWriter(HOME_DIR+VIDEO_DIR+"/"+video_file_name, fourcc, fps, (res_x,res_y))
        global is_recording 
        is_recording= True
        print("Starting video...")
        while is_recording == True:
            time.sleep(1.0/fps)                
            video_file.write(frame_date)
            n_frames=n_frames+1
            n_frames_max=n_frames_max+1
            if(n_frames/fps>=default_video_time):
                is_recording=False
            if(n_frames_max/fps>=max_time):
                video_file.release()
                n_frames_max=0
                video_file_name=get_data()+".avi"
                video_file = cv2.VideoWriter(HOME_DIR+VIDEO_DIR+"/"+video_file_name, fourcc, fps, (res_x,res_y))
        video_file.release()
        n_frames=0
        print("Ending video")

#function that start the video recording
recording_thread = None
@app.route('/start_video')
def start_video():
    global recording_thread
    recording_thread = threading.Thread(target=recording, args=(mutex,))
    recording_thread.start() #create a thread to record the video       
    return "True"

#function that start the temporized video recording
default_video_time=10
@app.route('/timer_video', methods=['POST'])
def timer_video():
    global default_video_time
    global recording_thread
    data = request.json
    text = data['text']
    try:
        default_video_time = float(text)  # Convert the string to a floating-point number
    except ValueError:
        default_video_time = 10 # Return 10 if the string is not a valid number
    # Process the text here (you can modify parameters or perform any other action)
    print(default_video_time)
    recording_thread = threading.Thread(target=recording_time, args=(mutex,))
    recording_thread.start() #create a thread to record the video       
    return "True"

#function that stop the video recording
@app.route('/stop_video')
def stop_video():
    global is_recording
    global n_frames
    is_recording=False
    recording_thread.join()
    print("sending video: " + video_file_name)
    n_frames=0
    return send_from_directory(HOME_DIR+VIDEO_DIR+"/" , video_file_name , as_attachment=True)

#function that change the home_folder
@app.route('/change_folder', methods=['POST'])
def change_folder():
    global HOME_DIR
    data = request.json
    text = data['text']
    print(text)
    if os.path.exists(text) and os.path.isdir(text):
        HOME_DIR=text
    else:
        HOME_DIR=DEFAULT_DIR
    create_dirs()
    return "True"

#function that resets the camera 
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


def change_dir():
    global HOME_DIR
    

#create photo and video dirs
def create_dirs():
    try:
        os.mkdir(HOME_DIR+PHOTO_DIR)
    except:
        print("photo dir already exists")
    try:
        os.mkdir(HOME_DIR+VIDEO_DIR)
    except:
        print("video dir already exists")
    

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
    create_dirs()
    app.run(debug=False)

@app.route('/photos/<filename>')
def get_photo(filename):
    # Serve the requested photo file
    return send_from_directory(HOME_DIR+PHOTO_DIR+"/", filename)

# Function to extract date from filename
def extract_date(filename):
    date_str = filename[:-4]  # Remove the extension
    return datetime.strptime(date_str, "%d%m%Y%H%M%S")

# Sort the list of file names based on the photo dir
@app.route('/get_photos_list')
def get_photos_list():
    # Get the list of photo files in the directory
    photo_files_aux = os.listdir(HOME_DIR+PHOTO_DIR+"/")
    photo_files=[]
    for file in photo_files_aux:
            if file.endswith(".jpg"):
                photo_files.append(file)
    photo_files = sorted(photo_files, key=extract_date, reverse=True)
    return jsonify(photo_files)


if __name__ == "__main__":
    main_thread = threading.Thread(target=main)  #create main theread than handles the web interface
    main_thread.start() # start the main thread
    
    
    