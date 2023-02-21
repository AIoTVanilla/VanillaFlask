from flask import Flask, render_template, session, Response
from library.database import *
import numpy as np
import datetime
import random
from flask_socketio import SocketIO, emit
import eventlet
import time
import threading
from library.yolo_manager import get_last_frame, show, get_snack_data
import json
from library.database import save_snack_log, save_speaker_log

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vanilla'
DID = 'd000001'
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)
    session.modified = True

@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@app.route("/monitor", methods=['POST', 'GET'])
def monitor():
    return render_template('monitor.html')

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

@app.route("/board", methods=['POST', 'GET'])
def board():
    return render_template('board.html')

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
    save_speaker_log('request_snack_count', json.dumps(data))
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
    save_speaker_log('request_snack_list', json.dumps(data))
    return data

@app.route('/request_favorite_snack', methods=['GET'])
def request_favorite_snack():
    print(random.sample(snack_list, 3))
    data = {
        "success": True,
        "result": random.sample(snack_list, 3)
    }
    save_speaker_log('request_favorite_snack', json.dumps(data))
    return data

@socketio.on('snack_tracking')
def snack_tracking():
    print("tracking!!!")

def ping_in_intervals():
    count = 0
    snack_status = False
    while True:
        socketio.sleep(1)
        # socketio.emit('snack', {
        #     'success': True,
        #     'result': bool(snack_status)
        # })
        socketio.emit('log', {
            'time': datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            'result': get_snack_data()
        })
        socketio.emit('frame', get_last_frame())
        snack_data = get_snack_data()
        save_snack_log(snack_data)
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

if __name__ == '__main__':
    thread = threading.Thread(target=show, args=())
    thread.daemon = True
    thread.start()

    snack_list = ["chicken_legs", "kancho", "rollpoly", "ramen_snack", "whale_food"]

    # app.run('0.0.0.0', 9999, debug=False)
    thread = socketio.start_background_task(ping_in_intervals)
    eventlet.wsgi.server(eventlet.listen(('', 7777)), app)