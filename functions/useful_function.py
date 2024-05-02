import os

def get_default_folder():
    no_user_name=False
    try:
        USER_NAME=os.getlogin()
        PRIMARY_FOLDER="/home/" + USER_NAME   
    except:
        no_user_name=True
        PRIMARY_FOLDER="/opt/"

    PICTURES_FOLDER="/Pictures"
    PROTO_0_FOLDER="/Proto-0_Camera"
    if not no_user_name:
        try:
            os.mkdir(PRIMARY_FOLDER+PICTURES_FOLDER)
        except:
            print(PICTURES_FOLDER + " dir already exists")
        PRIMARY_FOLDER=PRIMARY_FOLDER+PICTURES_FOLDER

        try:
            os.mkdir(PRIMARY_FOLDER+PROTO_0_FOLDER)
        except:
            print(PROTO_0_FOLDER + " dir already exists")
        PRIMARY_FOLDER=PRIMARY_FOLDER+PROTO_0_FOLDER
    else:
        PICTURES_FOLDER="proto-0_camera_pictures"
        try:
            os.mkdir(PRIMARY_FOLDER+PICTURES_FOLDER)
        except:
            print(PICTURES_FOLDER + " dir already exists")
        PRIMARY_FOLDER=PRIMARY_FOLDER+PICTURES_FOLDER
        
    return PRIMARY_FOLDER