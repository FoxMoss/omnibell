from uuid import uuid4
from flask import Flask, session, render_template
from flask_sock import Sock
import json

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

@app.route('/')
def index():
    # main html file
    return render_template('index.html')
