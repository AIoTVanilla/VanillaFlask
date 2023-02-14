from flask import Flask, request, render_template, session
from database import *
import numpy as np
import datetime
import random

app = Flask(__name__)

app.config['SECRET_KEY'] = 'aiot'
DID = 'd000001'

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
    app.run('0.0.0.0',9999, debug=True)