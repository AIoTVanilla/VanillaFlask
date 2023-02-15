from flask import Flask, request, render_template, session
from database import *
import numpy as np
import datetime
import random
import json
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vanilla'
DID = 'd000001'
socketio = SocketIO(app, cors_allowed_origins=['192.168.50.151:9999'])
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

@app.route('/test')
def test():
    return render_template('test.html',**values)

@app.route('/chat')
def chat():
    return render_template('chat.html')



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
            {"name": "s1", "count": get_snack_count("s1")},
            {"name": "s2", "count": get_snack_count("s2")},
            {"name": "s3", "count": get_snack_count("s3")},
            {"name": "s4", "count": get_snack_count("s4")},
            {"name": "s5", "count": get_snack_count("s5")},
        ]
    }
    return data

@app.route('/request_favorite_snack', methods=['GET'])
def request_favorite_snack():
    snacks = ["s1", "s2", "s3", "s4", "s5"]
    print(random.sample(snacks, 3))
    data = {
        "success": True,
        "result": random.sample(snacks, 3)
    }
    return data

@app.route('/send', methods=['POST'])
def send():
    jsonobj_content = request.json
    socketio.emit('server_response',  {'data':str(jsonobj_content)}, broadcast=True)
    return '', 200

@socketio.on('my event', namespace='/hello')
def hello():
    emit('my response', {'data': 'got it!'})
    return "11"

@socketio.on('connected_event')
def connected(msg):
    emit('server_response', {'data': msg['data']})

@socketio.on('broadcast_event')
def broadcast(msg):
    emit('server_response', {'data': msg['data']}, broadcast=True)

values = {
    'slider1': 25,
    'slider2': 0,
}
@socketio.on('connect')
def test_connect():
    emit('after connect',  {'data':'Lets dance'})

@socketio.on('slider')
def value_changed(message):
    values[message['who']] = message['data']
    print("value_changed")
    emit('update value', message, broadcast=True)

@socketio.on('message')
def message(data):
    print(data)  # {'from': 'client'}
    emit('response', {'from': 'server'})

def messageReceived(methods=['GET', 'POST']):
    print('message was received!!!')

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)

@socketio.on('my event')
def handle_my_custom_event(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    socketio.emit('my response', json, callback=messageReceived)



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
    # socketio.init_app(app, cors_allowed_origins="*") 
    socketio.run(app, '0.0.0.0', 9999, debug=True)