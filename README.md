# camera_protozero
To run the code just to python3 cam.py
Keyboard commands:
q - quit
p - take a picture

the cam.py was the prototype
It saves the pictures at the folder photo at same directory of the main script

Now there is the web application version:
To run: 
python3 cam_online.py

For more informations write -h for the parser info




----------------------------------
The camera is found automatically searching at the folder /sys/class/video4linux
If is needed to change the camera, its needed to change at the code the variable camera_name
Now it is:  camera_name="HD USB Camera"
The name can be found at: /sys/class/video4linux/videoi/name, which the i at videoi is the number that your camera is seen by the operational system
