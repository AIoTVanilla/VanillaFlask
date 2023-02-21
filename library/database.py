import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
import os
import socket
from collections import Counter

# Use a service account.
# /Users/suyoung/Documents/dev/aiot/AIoTClass/webapp/aiot-nuguna-03687aeaa9e6.json

last_snack_count = Counter([])
json_path = os.path.join(os.path.dirname(__file__).replace('library', ''), 'vanilla-3a108-firebase-adminsdk-ysr0t-9ce51811c0.json')
cred = credentials.Certificate(json_path)
app = firebase_admin.initialize_app(cred)

db = firestore.client()
print(firebase_admin.get_app())
print(socket.gethostname())

def save_speaker_log(command, result):
    doc_ref = db.collection('speaker').document()
    data = {
        "command": command,
        "result": result,
        "execute_time": firestore.firestore.SERVER_TIMESTAMP
    }
    doc_ref.set(data)

def get_snack_count(snack_status):
    return Counter(snack_status)

def save_snack_log(snack_status):
    global last_snack_count
    snack_count = get_snack_count(snack_status)

    if dict(snack_count) !=  dict(last_snack_count):
        data = {
            "chicken_legs": snack_count['chicken_legs'],
            "kancho": snack_count['kancho'],
            "rollpoly": snack_count['rollpoly'],
            "ramen_snack": snack_count['ramen_snack'],
            "whale_food": snack_count['whale_food'],
            "execute_time": firestore.firestore.SERVER_TIMESTAMP
        }
        db.collection('snack').document().set(data)

        s_copy = snack_count.copy()
        s_copy.subtract(last_snack_count)
        changes = {
            "chicken_legs": s_copy['chicken_legs'],
            "kancho": s_copy['kancho'],
            "rollpoly": s_copy['rollpoly'],
            "ramen_snack": s_copy['ramen_snack'],
            "whale_food": s_copy['whale_food'],
            "execute_time": firestore.firestore.SERVER_TIMESTAMP
        }
        db.collection('warehouse').document().set(changes)

        last_snack_count = snack_count


def get_device(d_id):
    device = db.collection('mdevice').document(d_id).get()
    if device.exists:
        return device.to_dict()

def create_device(d_id):
    doc_ref = db.collection('mdevice').document(d_id)
    if not doc_ref.get().exists:
        device = {d_id: {
            'id': d_id,
            'is_running': False,
            'manufacture_date': '20221213',
            'sensor': []
        }}
        doc_ref.set(device)


def upload_sensor(d_id, sensor):
    doc_ref = db.collection('mdevice').document(d_id)
    sensor['update_time'] = datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    doc_ref.update({'sensor': firestore.ArrayUnion([sensor])})





