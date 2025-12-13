from uuid import uuid4
from flask import Flask, session, render_template, request
from flask_sock import Sock
import json
import base64
import datetime
import uuid 
import time

app = Flask(__name__)
sock = Sock(app)

connections = {}
notifications = {}
doors = {}

server_stats = {
    "up_since": time.time(),
    "total_sent": 0,
    "total_rings": 0,
    "total_messages": 0,
    "ring_to_message_ratio": 0
}

@app.route('/stats')
def stats():
    return server_stats


# implements the ntfy protocol
# https://docs.ntfy.sh/subscribe/api/
@sock.route('/ntfy/<string:door>/ws')
def ntfy(ws, door):
    door_name = base64.b64decode(door).decode("utf-8")

    print(f"ntfy connected to {door}")
    ws.send(json.dumps({"id": str(uuid4()), "time": round(time.time()), "event": "open", "topic": door_name }))
    if(door not in doors):
        doors[door_name ] = DOOR_TEMPLATE.copy()
    try:
        doors[door_name ]["notification_listeners"].append(ws)
        while True:
            data = ws.receive()
    finally: 
        ws.close()
        doors[obj["door"]]["notification_listeners"].pop(doors[obj["door"]]["notification_listeners"].index(ws))


@sock.route('/connect')
def echo(ws):
    while True:
        data = ws.receive()
        # try: 
        obj = json.loads(data)
        if(obj["type"] == "listen_to_door"):

            # map all door conenctions
            connections[ws] = obj["door"]

            # make sure door is initalized
            if(obj["door"] not in doors):
                doors[obj["door"]] = {"rings": 0, "messages": [], "notification_listeners": []}

            # send client info that has already happened
            ws.send(json.dumps({"type": "door_info", "door": obj["door"], "times_rang": doors[obj["door"]]["rings"], "messages": doors[obj["door"]]["messages"]}))
        elif(obj["type"] == "ring"):

            if(obj["door"] not in doors):
                doors[obj["door"]] = {"rings": 0, "messages": [], "notification_listeners": []}

            # update stats info
            server_stats["total_sent"] += 1
            if("message" in obj):
                server_stats["total_messages"] += 1
            else:
                server_stats["total_rings"] += 1
            if(server_stats["total_messages"] != 0):
                server_stats["ring_to_message_ratio"] = server_stats["total_rings"] / server_stats["total_messages"]

            # update door info
            doors[obj["door"]]["rings"] += 1

            # make the ring message a little more verbose
            processed_message = f"Ring at {datetime.datetime.now()}"
            if("message" in obj):
                processed_message = f"{obj['message']} at {datetime.datetime.now()}"

            # update history we store 10 messages
            doors[obj["door"]]["messages"].append(processed_message)
            if(len(doors[obj["door"]]["messages"]) > 10):
                doors[obj["door"]]["messages"].pop(0)

            # send notifications
            for notify_ws in doors[obj["door"]]["notification_listeners"]:
                notify_ws.send(json.dumps({"id": str(uuid4()), "time": round(time.time()), "event": "message", "topic": obj["door"], "message":processed_message}))

            # cloned so we can edit the base array
            connections_clone = connections.copy()

            # relay to normal clients
            for other_ws in connections_clone:
                if(connections_clone[other_ws] == obj["door"] and other_ws != ws):
                    try: 
                        other_ws.send(json.dumps({"type": "ring", "door": obj["door"], "message": processed_message}))
                    except:
                        connections.pop(other_ws)
        # except:
        #     # json parse failed
        #     connections.pop(ws)
        #     ws.close()
        #     break;

@app.route('/<string:door>')
@app.route('/')
def index(door=None):
    if(door == "favicon.ico"):
        return "no" # todo replace with image 

    door_name = "The General Door"
    try:
        if (door):
            door_name = base64.b64decode(door).decode("utf-8")
    except:
        door_name = "The General Door"

    # main html file
    return render_template('index.html', door_name=door_name)
