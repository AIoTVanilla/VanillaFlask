import cv2
from PIL import Image
import io
# from io import StringIO
import base64
import imutils
import torch
import numpy as np
from datetime import datetime
import platform

interval = 0  # sec
last_snack_status = []
last_frame = None
# model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, force_reload=False)
model = torch.hub.load("ultralytics/yolov5", "custom", path = "snack_n" , force_reload=False)
model.eval()
model.conf = 0.25  # confidence threshold (0-1)
model.iou = 0.45  # NMS IoU threshold (0-1) 
print("Yolo", model.iou, model.conf)

def get_last_frame():
    return last_frame

def get_snack_data():
    return last_snack_status

def check_yolo(targets):
    global last_snack_status, last_targets

    last_snack_status = targets['name'].tolist()
    pass

def frameToYolo(frame):
    ret, buffer = cv2.imencode('.jpg', frame)
    frame = buffer.tobytes()
    
    img = Image.open(io.BytesIO(frame))
    results = model(img, size=640)

    targets = results.pandas().xyxy[0]
    check_yolo(targets)

    img = np.squeeze(results.render())
    img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    return img_BGR

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1920,
    capture_height=1080,
    display_width=640,
    display_height=360,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d !"
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def show():
    global last_frame
    t1 = datetime(1000, 1, 1)

    window_title = 'vanilla_monitor'
    video_capture = cv2.VideoCapture(1)
    is_mac = platform.system() == "Darwin"
    # video_capture = cv2.VideoCapture(gstreamer_pipeline(flip_method=0), cv2.CAP_GSTREAMER)
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    
    # video_capture = cv2.VideoCapture(0, cv2.CAP_GSTREAMER)
    # video_capture = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if video_capture.isOpened():
        try:
            if is_mac == False:
                window_handle = cv2.namedWindow(window_title, cv2.WINDOW_AUTOSIZE)
            while True:
                t2 = datetime.now()
                dt = (t2 - t1).total_seconds()

                if dt > interval:
                    ret_val, frame = video_capture.read()

                    start_ts = datetime.now()
                    img_BGR = frameToYolo(frame)
                    if is_mac == False:
                        cv2.imshow(window_title, img_BGR)

                    frame = imutils.resize(img_BGR, width=180)
                    frame = cv2.flip(frame, 1)
                    imgencode = cv2.imencode('.png', img_BGR)[1]
                    stringData = base64.b64encode(imgencode).decode('utf-8')
                    last_frame = 'data:image/png;base64,' + stringData
                    print(datetime.now() - start_ts)

                    t1 = t2
                    # yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

                    if is_mac == False:
                        keyCode = cv2.waitKey(10) & 0xFF
                        if keyCode == 27 or keyCode == ord('q'):
                            break
        except Exception as error:
            print("Error::", error)
        finally:
            video_capture.release()
            cv2.destroyAllWindows()
    else:
        print("Error: Unable to open camera")
