from uuid import uuid4
from flask import Flask, session, render_template, request
from flask_sock import Sock
import json
import base64

app = Flask(__name__)
sock = Sock(app)

@sock.route('/connect')
def echo(ws):
    while True:
        data = ws.receive()
        try: 
            obj = json.loads(data)

            if(obj["type"] == "listen_to_room"):
                pass # todo
            elif(obj["type"] == "ring"):
                pass # todo
        except:
            # json parse failed
            ws.close()
            break;

@app.route('/<string:room>')
@app.route('/')
def index(room=None):
    try:
        if (not room):
            room_name = "The General Door"
        else:
            room_name = base64.b64decode(room).decode("utf-8")
    except:
        room_name = "The General Door"

    # main html file
    return render_template('index.html', room_name=room_name)
