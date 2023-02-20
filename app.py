from flask import Flask, request, render_template, session, Response, make_response, redirect, url_for
from database import *
import numpy as np
import datetime
import random
from flask_socketio import SocketIO, emit
import eventlet
import torch
import cv2
from PIL import Image
import io
from io import StringIO
import base64
import imutils
import time
import threading


app = Flask(__name__)
app.config['SECRET_KEY'] = 'vanilla'
DID = 'd000001'
socketio = SocketIO(app, ping_in_intervals=2000)
socketio.init_app(app, cors_allowed_origins="*")

# model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True, force_reload=False)
model = torch.hub.load("ultralytics/yolov5", "custom", path = "snack" , force_reload=False)
model.eval()
model.conf = 0.25  # confidence threshold (0-1)
model.iou = 0.45  # NMS IoU threshold (0-1) 
print(model.iou, model.conf)

def capture_camera():
    print("capture_camera")
    
def gen():
    print("gen")
    cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
    # cap.set(cv2.CAP_PROP_FPS, 20)
    print("camera opened...", cap.isOpened())

    while(cap.isOpened()):
        # Capture frame-by-fram ## read the camera frame
        success, frame = cap.read()
        if success == True:
            ret, buffer=cv2.imencode('.jpg', frame)
            frame=buffer.tobytes()
            
            img = Image.open(io.BytesIO(frame))
            results = model(img, size=640)

            # print("--" * 20)
            targets = results.pandas().xyxy[0]
            if targets.empty == False:
                print(targets[['name']])
            # results.print()  # print results to screen

            img = np.squeeze(results.render()) #RGB
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2BGR) #BGR
        else:
            break

        frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()
        yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)
    session.modified = True

def send_file_data(data, mimetype='image/jpeg', filename='output.jpg'):
    response = make_response(data)
    response.headers.set('Content-Type', mimetype)
    response.headers.set('Content-Disposition', 'attachment', filename=filename)

    return response

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        fs = request.files.get('snap')
        if fs:
            img = cv2.imdecode(np.frombuffer(fs.read(), np.uint8), cv2.IMREAD_UNCHANGED)
            # img = detect_realtime_image(yolo, img)
            results = model(img, size=640)

            # print("--" * 20)
            targets = results.pandas().xyxy[0]
            if targets.empty == False:
                print(targets[['name']])
            # results.print()  # print results to screen

            # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # ret, buf = cv2.imencode('.jpg', img)
            img = np.squeeze(results.render()) #RGB
            img_BGR = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA) #BGR
            frame = cv2.imencode('.jpg', img_BGR)[1].tobytes()

            return send_file_data(frame)
        else:
            return 'You forgot Snap!'

    return redirect(url_for('index'))

@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@socketio.on('image')
def image(data_image):
    sbuf = StringIO()
    sbuf.write(data_image)

    # decode and convert into image
    b = io.BytesIO(base64.b64decode(data_image))
    pimg = Image.open(b)

    ## converting RGB to BGR, as opencv standards
    frame = cv2.cvtColor(np.array(pimg), cv2.COLOR_RGB2BGR)

    # Process the image frame
    frame = imutils.resize(frame, width=700)
    frame = cv2.flip(frame, 1)
    imgencode = cv2.imencode('.jpg', frame)[1]

    # base64 encode
    stringData = base64.b64encode(imgencode).decode('utf-8')
    b64_src = 'data:image/png;base64,'
    stringData = b64_src + stringData

    # emit the frame back
    emit('response_back', stringData)

@app.route('/video', methods=['POST', 'GET'])
def video():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/monitor/", methods=['POST', 'GET'])
def monitor():
    m = {
        "temp": 20,
        "humidity": 10,
        "water_level": 20,
        "ph": 7,
        "turbidity": 5,
        "fan": True
    }
    value = random.randrange(0, 4)
    g = get_growth(value)
    return render_template('monitor.html', m = m, growth = g)

def flask_logger():
    """creates logging information"""
    for i in range(100):
        # print(datetime.datetime.now().strftime('%H:%M:%S'))
        current_time = datetime.datetime.now().strftime('%H:%M:%S') + "\n"
        # log = current_time
        print(current_time, current_time.encode())
        yield current_time.encode()
        time.sleep(1)


@app.route("/log_stream", methods=['POST', 'GET'])
def log_stream():
    """returns logging information"""
    print("logging....")
    return Response(flask_logger(), mimetype="text/plain", content_type="text/event-stream")


@app.route("/board/<type>", methods=['POST', 'GET'])
def board(type = 'temp'):
    return render_template('board.html')

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/session')
def session():
    return render_template('session.html')

def get_snack_count(id):
    snack_count = random.randint(0, 5)
    return snack_count

@app.route('/hello', methods=['POST', 'GET'])
def hello():
    return "hello, vanilla"

@app.route('/request_snack_count', methods=['GET'])
def request_snack_count():
    snack_count = random.randint(0, 10)
    data = {
        "success": True,
        "result": snack_count
    }
    return data

@app.route('/request_snack_list', methods=['GET'])
def request_snack_list():
    data = {
        "success": True,
        "result": [
            {"name": snack_list[0], "count": get_snack_count("s1")},
            {"name": snack_list[1], "count": get_snack_count("s2")},
            {"name": snack_list[2], "count": get_snack_count("s3")},
            {"name": snack_list[3], "count": get_snack_count("s4")},
            {"name": snack_list[4], "count": get_snack_count("s5")},
        ]
    }
    return data

@app.route('/request_favorite_snack', methods=['GET'])
def request_favorite_snack():
    print(random.sample(snack_list, 3))
    data = {
        "success": True,
        "result": random.sample(snack_list, 3)
    }
    return data

@socketio.on('connect')
def test_connect():
    socketio.emit('response',  {'result': True})

@socketio.on('snack_tracking')
def snack_tracking():
    print("tracking!!!")

def ping_in_intervals():
    count = 0
    snack_status = False
    while True:
        socketio.sleep(5)
        # socketio.emit('snack', {
        #     'success': True,
        #     'result': bool(snack_status)
        # })
        socketio.emit('log', {
            'success': True,
            'time': datetime.datetime.now().strftime("%Y%m%d %H%M%S"),
            'result': bool(snack_status)
        })
        snack_status = snack_status == False

@app.teardown_request
def shutdown_session(exception=None):
    pass

def get_growth(growth):
    if growth == 0:
        return '씨앗'
    elif growth == 1:
        return '새싹'
    elif growth == 2:
        return '성장'
    elif growth == 3:
        return '성숙'

def get_monitor(sensor):
    if sensor['water_level'] == 0:
        water_level = '부족상태'
    else:
        water_level = '유지상태'
    turbidity = -1120.4 * np.square(sensor['turbidity']) + 5742.3 * sensor['turbidity'] - 4352.9
    if 'fan' in sensor:
        if sensor['fan'] == 'on':
            fan = '회전'
        else:
            fan = '비회전'
    else:
        fan = '비회전'
    return {
        'temp' : '{}℃'.format(sensor['temperature']),
        'humidity' : '{}%'.format(sensor['humidity']),
        'water_level' : '{}'.format(water_level),
        'ph' : '{}pH'.format(sensor['ph']),
        'turbidity' : '{:.2f}ntu'.format(turbidity),
        'fan' : '{}중'.format(fan),
    }

def get_board(device):
    cnt = len(device['sensor'])
    if cnt >20:
        cnt = 20
        sensors = device['sensor'][-20:]
        sensors.reverse()
        timeline = [sensor['update_time'] for sensor in sensors][-20:]

    else:
        sensors = device['sensor']
        sensors.reverse()
        timeline = [sensor['update_time'] for sensor in sensors]

    # print(sensors)
    msensors = [get_monitor(sensor) for sensor in sensors]

    return msensors, timeline

def get_chart(device, type):
    cnt = len(device['sensor'])
    if cnt > 20:
        cnt = 20
        sensors = device['sensor'][-20:]
        sensors.reverse()
    else:
        sensors = device['sensor']
        sensors.reverse()

    if type == 'temp':
        return [sensor['temperature'] for sensor in sensors]
    elif type == 'humidity':
        return [sensor['humidity'] for sensor in sensors]
    elif type == 'ph':
        return [sensor['ph'] for sensor in sensors]
    elif type == 'turbidity':
        return [sensor['turbidity'] for sensor in sensors]
    

img = []
cap = None
app_not_done = True

@app.route("/cap_img")
def cap_img():
    retval, buffer = cv2.imencode('.png', img)
    response = make_response(buffer.tobytes())
    response.headers['Content-Type'] = 'image/png'
    return response


class CameraThread(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        global img
        global app_not_done

        print("+++++++++ SETTING UP CAMERA ++++++++")
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cnt = 0
        while(app_not_done):
            # Capture frame-by-frame
            ret, frame = cap.read()
            if ret:
                img = frame
            else:
                cnt += 1
                if cnt < 4:
                    print("Could not read camera")

        # When everything done, release the capture
        print("RELEASING CAMERA *******************")
        cap.release()



if __name__ == '__main__':
    thrd = CameraThread('camera_thread')
    thrd.daemon = True
    thrd.start()

    snack_list = ["chicken_legs", "kancho", "rollpoly", "ramen_snack", "whale_food"]

    # $ openssl genrsa 1024 > server.key
    # $ openssl req -new -x509 -nodes -sha1 -days 365 -key server.key > server.cert

    # openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

    # app.run('0.0.0.0', 9999, debug=False)

    thread = socketio.start_background_task(ping_in_intervals)
    # thread1 = socketio.start_background_task(gen)
    # server = eventlet.wrap_ssl(eventlet.listen(('0.0.0.0', 8888)), certfile='secrets/cert.pem', keyfile='secrets/key.pem', server_side=True)
    # eventlet.wsgi.server(server, app)
    eventlet.wsgi.server(eventlet.listen(('', 8888)), app)

    app_not_done = False
    thrd.join()
