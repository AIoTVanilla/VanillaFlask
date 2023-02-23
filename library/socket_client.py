import socketio

sio = socketio.Client()
sio.connect('ws://127.0.0.1:9999')

@sio.on('snack')
def snack(data):
    print('snack', data)

@sio.on('response')
def response(data):
    print('response', data) 
