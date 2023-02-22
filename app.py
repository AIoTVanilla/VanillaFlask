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
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'vanilla'
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

@app.route("/board", methods=['POST', 'GET'])
def board(data = None):
    print('--' * 20)
    snack_list = get_current_snack_list();
    recent_snack_count = get_data_in_hour('snack');
    recent_speaker_count = get_data_in_hour('speaker');
    recent_warehouse_items = get_data_in_hour('warehouse', return_count=False);
    json_data = {
        "total_snack_count": sum(snack_list.values()),
        "snack_count": get_current_call_count('snack'),
        "speaker_count": get_current_call_count('speaker'),
        "snack_count_in_hour": recent_snack_count,
        "speaker_count_in_hour": recent_speaker_count,
        "snack_list": snack_list,
        "recent_warehouse_items": recent_warehouse_items,
    }
    print('--' * 20)
    return render_template('board.html', data = json_data)

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
    snack_list = get_current_snack_list();
    data = {
        "success": True,
        "result": sum(snack_list.values())
    }
    save_speaker_log('request_snack_count', json.dumps(data))
    return data

@app.route('/request_snack_list', methods=['GET'])
def request_snack_list():
    snack_list = get_current_snack_list();
    data = {
        "success": True,
        "result": snack_list
    }
    save_speaker_log('request_snack_list', json.dumps(data))
    return data

@app.route('/request_favorite_snack', methods=['GET'])
def request_favorite_snack():
    recent_warehouse_items = get_data_in_hour('warehouse', return_count=False);
    items = recent_warehouse_items["outgoing"]
    top_3_index = np.argsort(list(items.values()))[2:]
    keys = list(items.keys())
    data = {
        "success": True,
        "result": [keys[int(top_3_index[0])], keys[int(top_3_index[1])], keys[int(top_3_index[2])]],
    }
    save_speaker_log('request_favorite_snack', json.dumps(data))
    return data

def ping_in_intervals():
    has_snack = False
    snack_check_count = 0
    
    while True:
        socketio.sleep(1)

        snack_data = get_snack_data()
        socketio.emit('log', {
            'time': datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
            'result': snack_data
        })
        socketio.emit('frame', get_last_frame())
        save_snack_log(snack_data)

        snack_size = len(snack_data)
        if snack_size > 0:
            if snack_check_count == 10:
                socketio.emit('snack', { 'success': True, 'result': True })
                socketio.emit('log', {
                    'time': datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                    'message': "snack is incoming..."
                })
            if snack_check_count < 0: snack_check_count = 0
            else: snack_check_count += 1
        elif snack_size == 0:
            if snack_check_count == -10:
                socketio.emit('snack', { 'success': True, 'result': False })
                socketio.emit('log', {
                    'time': datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                    'message': "snack is outgoing..."
                })
            if snack_check_count > 0: snack_check_count = 0
            else: snack_check_count -= 1

@app.teardown_request
def shutdown_session(exception=None):
    pass

if __name__ == '__main__':
    thread = threading.Thread(target=show, args=())
    thread.daemon = True
    thread.start()

    snack_list = ["chicken_legs", "kancho", "rollpoly", "ramen_snack", "whale_food"]

    # app.run('0.0.0.0', 9999, debug=False)
    thread = socketio.start_background_task(ping_in_intervals)
    eventlet.wsgi.server(eventlet.listen(('', 7777)), app)