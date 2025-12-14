from uuid import uuid4
from flask import Flask, session, render_template, request, stream_with_context
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


# implements the websocket ntfy protocol
# https://docs.ntfy.sh/subscribe/api/
@sock.route('/ntfy/<string:door>/ws')
def ntfy(ws, door):
    door_name = base64.b64decode(door.replace("-", "=")).decode("utf-8")

    print(f"ntfy connected to {door}")
    ws.send(json.dumps({"id": door, "time": round(time.time()), "event": "open", "topic": door_name }))
    if(door not in doors):
        doors[door_name] = {"rings": 0, "messages": [], "notification_listeners": []}

    try:
        doors[door_name]["notification_listeners"].append(ws)
        while True:
            data = ws.receive()
    finally: 
        ws.close()
        doors[obj["door"]]["notification_listeners"].pop(doors[obj["door"]]["notification_listeners"].index(ws))

new_packets = []

# WIP: http stream support
@app.route('/ntfy/<string:door>/json')
def ntfy_stream(door):
    # ntfy doesnt like = in ids
    door_name = base64.b64decode(door.replace("-", "=")).decode("utf-8")

    if(request.args.get('poll')):
        can_read = True
        since = ""
        if(request.args.get('since') and request.args.get('since') != door and request.args.get('since') != "all"):
            can_read = False
            since = request.args.get('since')

        ret = ""
        for packets in new_packets:
            if(packets["id"] == since):
                can_read = True
                continue

            if(packets["topic"] != door_name):
                continue

            if(not can_read):
                continue

            ret += json.dumps(packets) + "\n"
        return ret

    read_packets_id = []

    def stream():
        print(f"ntfy connected to {door}")
        yield json.dumps({"id": str(uuid4()), "time": round(time.time()), "event": "open", "topic": door_name }) + "\n"
        if(door not in doors):
            doors[door_name] = {"rings": 0, "messages": [], "notification_listeners": []}

        while True:
            for packet in new_packets:
                if(new_packets["id"] in read_packets_id):
                    continue
                if(new_packets["topic"] != door_name):
                    continue
                yield json.dumps(packet) + "\n"
                read_packets_id.append(new_packets["id"])

            time.sleep(1)
    return stream_with_context(stream())

@app.route('/ntfy/<string:door>/auth')
def ntfy_auth(door):
    door_name = base64.b64decode(door.replace("-", "=")).decode("utf-8")

    return {"success": True}

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

            notify_packet = {"id": str(uuid4()), "time": round(time.time()), "event": "message", "topic": obj["door"], "message":processed_message}

            # send notifications
            for notify_ws in doors[obj["door"]]["notification_listeners"]:
                notify_ws.send(json.dumps(notify_packet))

            new_packets.append(notify_packet)


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
