import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime, timezone, timedelta
import os
import socket
from collections import Counter
from google.api_core.datetime_helpers import DatetimeWithNanoseconds
import time
import pandas as pd

last_snack_count = Counter([])
json_path = os.path.join(os.path.dirname(__file__).replace('library', ''), 'vanilla-3a108-firebase-adminsdk-ysr0t-9ce51811c0.json')
cred = credentials.Certificate(json_path)
app = firebase_admin.initialize_app(cred)
db = firestore.client()

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

def get_current_hour_timestamp():
    date_time = datetime.now()
    timestamp = time.mktime(date_time.timetuple())
    timestamp = int(timestamp - (timestamp % 3600))
    return timestamp

def save_snack_log(snack_status):
    global last_snack_count
    snack_count = get_snack_count(snack_status)
    timestamp = get_current_hour_timestamp()

    if dict(snack_count) !=  dict(last_snack_count):
        data = {
            "chicken_legs": snack_count['chicken_legs'],
            "kancho": snack_count['kancho'],
            "rollpoly": snack_count['rollpoly'],
            "ramen_snack": snack_count['ramen_snack'],
            "whale_food": snack_count['whale_food'],
            "execute_time": firestore.firestore.SERVER_TIMESTAMP
        }
        doc_ref = db.collection('snack').document(str(timestamp))
        if doc_ref.get().exists:
            doc_ref.update(data)
        else:
            doc_ref.create(data)

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

def get_current_call_count(path):
    current_date = datetime.now()
    ts = DatetimeWithNanoseconds(current_date.year, current_date.month, current_date.day, 0, 0, 0, 0, tzinfo=timezone(timedelta(hours=9)))

    items = db.collection(path).order_by('execute_time').start_at({
        "execute_time": ts
    }).get()
    return len(items)

def sum_by_key(df, key, is_plus):
    if is_plus:
        value = sum(df[df[key] > 0][key])
        return value if value > 0 else 0
    else:
        value = sum(df[df[key] < 0][key])
        return value if value < 0 else 0

def get_str_value(value, is_plus):
    if is_plus:
        return ("+" + str(value)) if value > 0 else "+0"
    else:
        return str(value) if value < 0 else "-0"

def get_data_in_hour(path, return_count = True):
    current_date = datetime.now() - timedelta(hours=1)
    ts = DatetimeWithNanoseconds(current_date.year, current_date.month, current_date.day, current_date.hour, current_date.minute, 0, 0, tzinfo=timezone(timedelta(hours=9)))

    items = db.collection(path).order_by('execute_time').start_at({
        "execute_time": ts
    }).get()
    # size = len(items)
    # return size, items[-1].to_dict() if size > 0 else {}

    if return_count:
        return len(items)
    else:
        warehouse_data = []
        for item in items:
            warehouse_data.append(item.to_dict())
        
        df = pd.DataFrame(warehouse_data)

        chicken_legs_incoming = sum_by_key(df, "chicken_legs", True)
        kancho_incoming = sum_by_key(df, "kancho", True)
        ramen_snack_incoming = sum_by_key(df, "ramen_snack", True)
        rollpoly_incoming = sum_by_key(df, "rollpoly", True)
        whale_food_incoming = sum_by_key(df, "whale_food", True)

        chicken_legs_outgoing = last_snack_count["chicken_legs"] - int(chicken_legs_incoming)
        kancho_outgoing = last_snack_count["kancho"] - int(kancho_incoming)
        ramen_snack_outgoing = last_snack_count["ramen_snack"] - int(ramen_snack_incoming)
        rollpoly_outgoing = last_snack_count["rollpoly"] - int(rollpoly_incoming)
        whale_food_outgoing = last_snack_count["whale_food"] - int(whale_food_incoming)

        incoming_count = sum([chicken_legs_incoming, kancho_incoming, ramen_snack_incoming, rollpoly_incoming, whale_food_incoming])
        # outgoing_count = sum([chicken_legs_outgoing, kancho_outgoing, ramen_snack_outgoing, rollpoly_outgoing, whale_food_outgoing])

        return {
            "incoming_count": get_str_value(incoming_count, True),
            # "outgoing_count": get_str_value(outgoing_count, False),
            "incoming": {
                "chicken_legs": get_str_value(chicken_legs_incoming, True),
                "kancho": get_str_value(kancho_incoming, True),
                "ramen_snack": get_str_value(ramen_snack_incoming, True),
                "rollpoly": get_str_value(rollpoly_incoming, True),
                "whale_food": get_str_value(whale_food_incoming, True),
            },
            "outgoing": {
                "chicken_legs": get_str_value(chicken_legs_outgoing, False),
                "kancho": get_str_value(kancho_outgoing, False),
                "ramen_snack": get_str_value(ramen_snack_outgoing, False),
                "rollpoly": get_str_value(rollpoly_outgoing, False),
                "whale_food": get_str_value(whale_food_outgoing, False),
            },

        }

def get_current_snack_list():
    timestamp = get_current_hour_timestamp()
    doc = db.collection('snack').document(str(timestamp)).get()

    dict = doc.to_dict()
    del dict["execute_time"]
    return dict if doc.exists else {
        'chicken_legs': 0,
        'kancho': 0,
        'ramen_snack': 0,
        'rollpoly': 0,
        'whale_food': 0,
    }

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





