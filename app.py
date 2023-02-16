from flask import Flask, request, render_template, session
from database import *
import numpy as np
import datetime
import random
from flask_socketio import SocketIO
import eventlet

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vanilla'
DID = 'd000001'
socketio = SocketIO(app, ping_in_intervals=2000)
socketio.init_app(app, cors_allowed_origins="*")

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=5)
    session.modified = True

@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@app.route("/monitor/", methods=['POST', 'GET'])
def monitor():
    if 'd' not in session:
        session['d'] = get_device(DID)
    device = session['d']
    m = get_monitor(device['sensor'][-1])
    value = random.randrange(0, 4)
    print(value)
    g = get_growth(value)

    # g = get_growth(device['growth']) 
    return render_template('monitor.html', m = m, growth = g)

@app.route("/board/<type>", methods=['POST', 'GET'])
def board(type = 'temp'):
    if 'd' not in session:
        session['d'] = get_device(DID)
    device = session['d']
    sensors, times = get_board(device)
    values = get_chart(device, type)
    return render_template('board.html', sensors = sensors , times = times, values = values)

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == "GET":
        return render_template('sregister.html')
    else:
        sId = request.form['sId']
        if len(sId) > 0:
            create_device(sId)
        return render_template('index.html')

@app.route('/session')
def sessions():
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

def messageReceived():
    print('message was received!!!')

@socketio.on('request')
def handle_my_custom_event(json):
    print('received request: ' + str(json))
    socketio.emit('response', json, callback=messageReceived)

@socketio.on('connect')
def test_connect():
    socketio.emit('response',  {'result': True})

@socketio.on('snack_tracking')
def snack_tracking():
    print("tracking!!!")

def ping_in_intervals():
    snack_status = False
    while True:
        socketio.sleep(10)
        socketio.emit('snack', {
            'success': True,
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

if __name__ == '__main__':
    snack_list = ["chicken_legs", "kancho", "rollpoly", "ramen_snack", "whale_food"]

    # app.run('0.0.0.0', 9999, debug=False)
    thread = socketio.start_background_task(ping_in_intervals)
    eventlet.wsgi.server(eventlet.listen(('', 9999)), app)
