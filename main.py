from notification import Notification, NotificationTo
from typing import Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import vehicle
import uuid
import asyncio
from collections import defaultdict, deque
import socketio
import bidict
from a2wsgi import ASGIMiddleware
from rich import print
from geopy.distance import distance


app = FastAPI()
sio = socketio.Server()
socket_app = socketio.WSGIApp(sio, ASGIMiddleware(app))
# socket_app = socketio.WSGIApp(sio)


vehicles: Dict[str, vehicle.Vehicle] = {}
users = set()

notif_queue = deque()
notif_lock = None
notif_loc = None

user2vehicle = {}
vehicle2user = defaultdict(list)

vehicles["Vasista's Car"] = vehicle.Vehicle()
vehicles["Vasista's Car"].id = "Vasista's Car"
vehicles["Vasista's Car"].name = "Vasista's Car"

vehicles["Vasista's Moto"] = vehicle.Vehicle()
vehicles["Vasista's Moto"].id = "Vasista's Moto"
vehicles["Vasista's Moto"].name = "Vasista's Moto"

user2vehicle["Vasista's Car"] = "Vasista's Car"
vehicle2user["Vasista's Car"].append("Vasista's Car")

@sio.on("connect")
def connect(sid, environ):
    print(f"User {sid} connected")

@sio.on("createvehicle")
def createvehicle(sid):
    vehicle_id = str(uuid.uuid4())
    vehicles[vehicle_id] = vehicle.Vehicle()
    setvehicle(sid, vehicle_id)
    # sio.emit("vehicle_id", vehicle_id, to=sid)
    print(f"User {sid} created {vehicle_id}")
    return vehicle_id


@sio.on("setvehicle")
def setvehicle(sid, vehicle_id):
    # user2vehicle[sid] = vehicle_id
    # vehicle2user[vehicle_id].append(sid)
    print(f"User {sid} is watching {vehicle_id}")

@sio.on("disconnect")
def disconnect(sid):
    try:
        vehicle2user.pop(user2vehicle[sid])
        del user2vehicle[sid]
        print(f"User {sid} disconnected")
    except Exception:
        pass

@sio.on("setfeatures")
def setfeatures(sid, data):
    if sid in user2vehicle:
        vid = user2vehicle[sid]
    else:
        vid = sid
    vehicles[vid].features = vehicles[vid].features.copy(update=data.dict(exclude_unset=True))
    print(f"User {sid} set {vid} features")

    for sid in vehicle2user[vid]:
        sio.emit("features", vehicles[vid].features.dict(),  to=sid)

@sio.on("setstate")
def setstate(sid, data):
    if sid in user2vehicle:
        vid = user2vehicle[sid]
    else:
        vid = sid
    vehicles[vid].state = vehicles[vid].state.copy(update=data.dict(exclude_unset=True))
    print(f"User {sid} set {vid} state")

    for sid in vehicle2user[vid]:
        sio.emit("state", vehicles[vid].state.dict(),  to=sid)

@app.get("/")
async def root():
    return {
        "hello": "world"
    }

@app.get("/newvehicle/{vehicle_name}")
async def put_new_vehicle( vehicle_name:str):
    vehicle_id = str(uuid.uuid4())
    # vehicles[vehicle_id] = vehicle.Vehicle()
    vehicles[vehicle_name] = vehicle.Vehicle()
    # vehicles[vehicle_id].id = vehicle_id
    vehicles[vehicle_name].id = vehicle_name
    vehicles[vehicle_name].name = vehicle_name
    print("VEHICLE ADDED")
    return vehicle_name


@app.get("/vehicles")
async def get_vehicles():
    return list(vehicles.values())

@app.get("/vehicle/{vehicle_id}", response_model=vehicle.Vehicle)
async def get_vehicle(vehicle_id: str, user_id: str = "0"):
    if vehicle_id not in vehicles:
        raise HTTPException(404, "Vehicle Not Found")
    v = vehicles[vehicle_id]
    # if user_id not in v.users:
        # raise HTTPException(404, "Vehicle Not Found")

    return vehicles[vehicle_id]

@app.put("/vehicle/{vehicle_id}")
async def put_vehicle(vehicle_id: str, data: vehicle.Vehicle):

    async def notif():
        await asyncio.sleep(3)
        if not vehicles[vehicle_id].state.locked:
            notif_lock = (
            # notif_queue.append(
                Notification(
                    title = "You left your vehicle unlocked!",
                    message = "Tap to lock your vehicle.",
                    to = NotificationTo.LOCK
                )
            )

    dist = distance(
        (vehicles[vehicle_id].state.location.latitude, vehicles[vehicle_id].state.location.longitude),
        (data.state.location.latitude, data.state.location.longitude)
    ).ft

    if dist > 5:
        notif_loc = (
        # notif_queue.append(
            Notification(
                title = "Your vehicle is moving!",
                message = "Tap to check the vehicle's location.",
                to = NotificationTo.GPS
            )
        )

    vehicles[vehicle_id] = data

    if data.state.notif_lock and vehicles[vehicle_id].state.locked and not data.state.locked:
        await notif()

@app.get("/vehicle/{vehicle_id}/features")
async def get_vehicle_features(vehicle_id: str):
    return get_vehicle(vehicle_id).features

@app.put("/vehicle/{vehicle_id}/features")
async def put_vehicle_features(vehicle_id: str, data: vehicle.VehicleFeatures):
    v = await get_vehicle(vehicle_id)
    v.features = v.features.copy(update=data)

@app.get("/vehicle/{vehicle_id}/state")
async def get_vehicle_state(vehicle_id: str):
    return get_vehicle(vehicle_id).state

@app.put("/vehicle/{vehicle_id}/state")
async def put_vehicle_state(vehicle_id: str, data: vehicle.VehicleState):
    v = await get_vehicle(vehicle_id)
    v.state = v.state.copy(update=data.dict(exclude_unset=True))

@app.get("/notification")
async def get_notification():
    global notif_lock
    global notif_loc
    # notif = notif_queue.pop()
    notif = notif_loc or notif_lock
    print(notif)
    if notif:
        notif_lock = None
        notif_loc = None
        print("Notification sent", notif)
        return notif

# while True: ...
@app.get("/notification/location")
async def put_location_notification():
    global notif_loc
    notif_loc = Notification(
        title = "Your vehicle is moving!",
        message = "Tap to check the vehicle's location.",
        to = NotificationTo.GPS
    )

@app.get("/notification/lock")
async def put_lock_notification():
    global notif_loc
    notif_loc = Notification(
        title = "You left your vehicle unlocked!",
        message = "Tap to lock your vehicle.",
        to = NotificationTo.LOCK
    )

@app.get("/notification/lockaway")
async def put_lockaway_notification():
    global notif_loc
    notif_loc = Notification(
        title = "Was this you? Your vehicle was just unlocked.",
        message = "Tap to lock your vehicle.",
        to = NotificationTo.LOCK
    )

loop = asyncio.get_event_loop()

async def check_timers():
    global notif_lock
    global notif_loc

    while True:
        await asyncio.sleep(10)
        print("Adding notif")
        # notif_loc = (
        #     Notification(
        #         title = "Your vehicle is moving!",
        #         message = "Tap to check the vehicle's location.",
        #         to = NotificationTo.GPS
        #     )
        # )
        print("q")

loop.create_task(check_timers())
# loop.run_forever()