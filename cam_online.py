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

import socket

#from gevent.pywsgi import WSGIServer
from functions.useful_function import get_default_folder
#compress video functions
from functions.compression import compress_video_GB

#Initialize the Flask app
app = Flask(__name__)
#camera name, check the name of your camera at /sys/class/video4linux/video(i)/name (OBRIGADO) 

camera_name= "Integrated RGB Camera: Integrat"#"EasyCamera: EasyCamera" #"HD USB Camera"
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
mutex_compression = threading.Lock()

#return the date in the format YYYY-MM-DD_HH-MM-SS
def get_data():
    now=datetime.now()
    dt_string = now.strftime("%Y-%m-%d_%H-%M-%S")
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

def gen_frames_thread():
    global success
    global frame, frame_date 
    global camera
    while True:
        if camera.isOpened():
            success, frame = camera.read()  # read the camera frame
            if not success:
                frame=generate_black()
        else:
            frame=generate_black()
            success=False
        frame_date = put_date(frame)
        time.sleep(1/fps)   
        

#function that generate frame from time to time
def gen_frames():
    global frame_date 
    while True:
        try:
            ret, buffer = cv2.imencode('.jpg', frame_date)
            frame_bytes = buffer.tobytes()
        except:
            print("oi")
            frame_bytes=0
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')  # concat frame one by one and show result
        time.sleep(1/fps)
        
#function that return the real time video to the web interface
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

#function that takes picture
@app.route('/take_picture')
def take_picture():
    
    print("Taking picture...")
    #ret, frame = camera.read()
    name=get_data()+"_proto-0_picture.jpg"
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
            name=get_data()+"_proto-0_timer_picture.jpg"
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
            if timer_video_check==True:
                yield "data: {}\n\n".format("VIDEO RECORDING ON -- Total time: {:.2f}s -- Now time: {:.2f}s -- File time: {:.2f}s".format(default_video_time, time_recording,default_video_time_file) if is_recording else "VIDEO RECORDING OFF")
            else:
                yield "data: {}\n\n".format("VIDEO RECORDING ON -- Total time: Forever -- Now time: {:.2f}s -- File time: {:.2f}s".format(time_recording,default_video_time_file) if is_recording else "VIDEO RECORDING OFF")
            time.sleep(1)  # Send status every 1 second
            #time.sleep(1)  # Simulate delay
    return Response(generate_video(), mimetype='text/event-stream')


is_recording=False
fps=30.0
fps_video=24

compression_thread=None
event_compression = threading.Event()
video_files_list=[]

#thread for compression
def compression_service(mutex_compression):
    global event_compression
    global video_files_list
    compress_factor=5
    name_list = []
    while True:
        event_compression.wait()
        event_compression.clear()
        with mutex_compression:
            while len(video_files_list) >0:
                name_list.append(video_files_list.pop(0))
        for name in name_list:
            compress_video_GB(HOME_DIR+VIDEO_DIR+"/"+name,compress_factor)
            time.sleep(1)
        name_list=[]


#preparing comprresion
def compression_init(name,mutex_compression,video_files_list,event_compression):
    with mutex_compression:
        video_files_list.append(name)
        event_compression.set()



#theread for recording the video
video_file_name = None
def recording(mutex,mutex_compression):
    global n_frames
    global video_file_name
    global timer_video_check
    global video_files_list
    global event_compression
    max_time=default_video_time_file #seconds
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_file = cv2.VideoWriter()
    with mutex:
        timer_video_check=False
        video_file_name=get_data()+"_proto-0_video.mp4"
        video_file = cv2.VideoWriter(HOME_DIR+VIDEO_DIR+"/"+video_file_name, fourcc, fps_video, (res_x,res_y))
        global is_recording 
        is_recording= True
        n_frames_max=0
        print("Starting video...")
        while is_recording == True:
            n_frames=n_frames+1
            n_frames_max=n_frames_max+1
            time.sleep(1.0/fps_video)                
            video_file.write(frame_date)
            if(n_frames_max/fps_video>=max_time):
                video_file.release()
                compression_init(video_file_name,mutex_compression,video_files_list,event_compression)
                #compress_video_GB(HOME_DIR+VIDEO_DIR+"/"+video_file_name,5)
                n_frames_max=0
                video_file_name=get_data()+"_proto-0_video.mp4"
                video_file = cv2.VideoWriter(HOME_DIR+VIDEO_DIR+"/"+video_file_name, fourcc, fps_video, (res_x,res_y))

        video_file.release()
        compression_init(video_file_name,mutex_compression,video_files_list,event_compression)
        n_frames=0
        print("Ending video")

n_frames=0
#thread for recording temporized videos
def recording_time(mutex,mutex_compression):
    global n_frames
    global timer_video_check
    n_frames=0
    max_time=default_video_time_file #seconds
    n_frames_max=0
    global video_file_name
    global video_files_list
    global event_compression
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_file = cv2.VideoWriter()
    with mutex:
        timer_video_check=True
        video_file_name=get_data()+"_proto-0_timer_video.mp4"
        video_file = cv2.VideoWriter(HOME_DIR+VIDEO_DIR+"/"+video_file_name, fourcc, fps_video, (res_x,res_y))
        global is_recording 
        is_recording= True
        print("Starting video...")
        while is_recording == True:
            time.sleep(1.0/fps_video)                
            video_file.write(frame_date)
            n_frames=n_frames+1
            n_frames_max=n_frames_max+1
            if(n_frames/fps_video>=default_video_time):
                is_recording=False
            if(n_frames_max/fps_video>=max_time):
                video_file.release()
                compression_init(video_file_name,mutex_compression,video_files_list,event_compression)                
                n_frames_max=0
                video_file_name=get_data()+"_proto-0_timer_video.mp4"
                video_file = cv2.VideoWriter(HOME_DIR+VIDEO_DIR+"/"+video_file_name, fourcc, fps_video, (res_x,res_y))
        video_file.release()
        compression_init(video_file_name,mutex_compression,video_files_list,event_compression)        
        n_frames=0
        print("Ending video")

#function that start the video recording
recording_thread = None
@app.route('/start_video',methods=['POST'])
def start_video():
    global recording_thread
    global compression_thread
    global default_video_time_file
    data = request.json
    text_i=data['text_i']
    try:
        default_video_time_file = float(text_i)  # Convert the string to a floating-point number
    except ValueError:
        default_video_time_file = 10*60 
    # Process the text here (you can modify parameters or perform any other action)

    recording_thread = threading.Thread(target=recording, args=(mutex,mutex_compression))
    recording_thread.start() #create a thread to record the video       
    compression_thread = threading.Thread(target=compression_service,args=(mutex_compression,))
    compression_thread.start()
    return "True"

#function that start the temporized video recording
default_video_time=5*60
default_video_time_file=10*60
timer_video_check=False
@app.route('/timer_video', methods=['POST'])
def timer_video():
    global default_video_time
    global default_video_time_file
    global compression_thread

    global recording_thread
    
    data = request.json
    text = data['text']
    text_i=data['text_i']
    try:
        default_video_time = float(text)  # Convert the string to a floating-point number
    except ValueError:
        default_video_time = 5*60 # Return 5 if the string is not a valid number

    try:
        default_video_time_file = float(text_i)  # Convert the string to a floating-point number
    except ValueError:
        default_video_time_file = 10*60 # Return 5 if the string is not a valid number
    # Process the text here (you can modify parameters or perform any other action)

    recording_thread = threading.Thread(target=recording_time, args=(mutex,mutex_compression))
    recording_thread.start() #create a thread to record the video
    compression_thread = threading.Thread(target=compression_service,args=(mutex_compression,))
    compression_thread.start()       
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
    
@app.route('/photos/<filename>')
def get_photo(filename):
    # Serve the requested photo file
    return send_from_directory(HOME_DIR+PHOTO_DIR+"/", filename)

# Function to extract date from filename
def extract_date(filename):
    date_str = filename[:-4]  # Remove the extension
    try:
        key=datetime.strptime(date_str, "%d/%m/%Y-%H:%M:%S")
    except:
        key=date_str
    return key

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


#start function that creates the web interface defined at index.html            
@app.route('/')
def index():
    return render_template('index.html')

video_Thread=None
def main(): #this is the main thread
    global success
    global camera
    global video_Thread
    camera = cv2.VideoCapture(cam_id,cv2.CAP_V4L) #variable that reads the camera
    if not camera.isOpened():
        print("Error: Could not open camera.")
        success=False
    else:
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, res_x)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, res_y)
    create_dirs()
    video_Thread = threading.Thread(target=gen_frames_thread)
    video_Thread.start()
    from waitress import serve
    serve(app,host='0.0.0.0',port=8080, threads=10)
        # Get the local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    # Print the local IP address and port
    print(f"Serving on http://{local_ip}:{port}")
    #app.run(host='0.0.0.0',port=5000,debug=False)


cam_id=find_camera_id(camera_name) #find the id of camera based on his name on the linux interface
if __name__ == "__main__":
    main_thread = threading.Thread(target=main)  #create main theread than handles the web interface
    main_thread.start() # start the main thread
    
    
    