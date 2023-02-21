import socketio

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    sio.send(f"\nClient {sio.sid} connected...\n")

@sio.on('response')
def receive_custom(msg):
    print(msg)

sio.connect('http://127.0.0.1:9999')
# sio.wait() # cannot keyboard interrupt this
sio.sleep(10)
sio.disconnect()