import cv2
import os
from datetime import datetime

def get_data():
    now=datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    print(dt_string)
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

def main():

    try:
        os.mkdir("photo")
    except OSError as error:  
        print(error)

    camera_name="HD USB Camera"
    device_id=find_camera_id(camera_name)

    # Open the specific camera
    cap = cv2.VideoCapture(device_id)

    # Check if the camera was opened successfully
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Loop to capture and display frames from the camera
    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()

        # Check if the frame was captured successfully
        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Display the frame
        cv2.imshow('USB Camera', frame)

        # Check for 'p' key to save the frame as an image
        key = cv2.waitKey(1)
        if key == ord('p'):
            # Save the frame as an image
            cv2.imwrite("photo/" + get_data()+".jpg", frame)

        # Check for 'q' key to exit the loop
        if key & 0xFF == ord('q'):
            break

    # Release the VideoCapture object and close all windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()