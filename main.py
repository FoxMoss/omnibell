from uuid import uuid4
from flask import Flask, session, render_template, request
from flask_sock import Sock
import json
import base64

app = Flask(__name__)
sock = Sock(app)

connections = {}
doors = {}

@sock.route('/connect')
def echo(ws):
    while True:
        data = ws.receive()
        try: 
            obj = json.loads(data)

            if(obj["type"] == "listen_to_door"):
                connections[ws] = obj["door"]
                if(obj["door"] not in doors):
                    doors[obj["door"]] = {"rings": 0, "messages": []};
                ws.send(json.dumps({"type": "door_info", "door": obj["door"], "times_rang": doors[obj["door"]]["rings"], "messages": doors[obj["door"]]["messages"]}))
            elif(obj["type"] == "ring"):
                doors[obj["door"]]["rings"] += 1
                connections_clone = connections.copy()
                if("message" in obj):
                    doors[obj["door"]]["messages"].append(obj["message"])
                    if(len(doors[obj["door"]]["messages"]) > 10):
                        doors[obj["door"]]["messages"].pop(0)
                for other_ws in connections_clone:
                    if(connections_clone[other_ws] == obj["door"] and other_ws != ws):
                        try: 
                            if "message" in obj:
                                other_ws.send(json.dumps({"type": "ring", "door": obj["door"], "message": obj["message"]}))
                            else:
                                other_ws.send(json.dumps({"type": "ring", "door": obj["door"]}))
                        except:
                            connections.pop(other_ws)
        except:
            # json parse failed
            connections.pop(ws)
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
