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


app = FastAPI()
sio = socketio.Server()
# socket_app = socketio.WSGIApp(sio, ASGIMiddleware(app))
socket_app = socketio.WSGIApp(sio)


vehicles: Dict[str, vehicle.Vehicle] = {}
users = set()

notif_queue = deque()

vehicles["test"] = vehicle.Vehicle()


user2vehicle = {}
vehicle2user = defaultdict(list)

user2vehicle["test"] = "test"
vehicle2user["test"].append("test")

@sio.on("connect")
def connect(sid, environ):
    print(f"User {sid} connected")

@sio.on("createvehicle")
def createvehicle(sid):
    vehicle_id = str(uuid.uuid4())
    vehicles[vehicle_id] = vehicle.Vehicle()
    setvehicle(sid, vehicle_id)
    sio.emit("vehicle_id", vehicle_id, to=sid)
    print(f"User {sid} created {vehicle_id}")


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

@app.post("/vehicle/")
async def put_vehicle( user_id: str = "0"):
    vehicle_id = str(uuid.uuid4())
    vehicles[vehicle_id] = vehicle.Vehicle()
    return vehicle_id


@app.get("/vehicles")
async def get_vehicles():
    print(list(vehicles.keys()))
    return list(vehicles.keys())

@app.get("/vehicle/{vehicle_id}", response_model=vehicle.Vehicle)
async def get_vehicle(vehicle_id: str, user_id: str = "0"):
    if vehicle_id not in vehicles:
        raise HTTPException(404, "Vehicle Not Found")
    v = vehicles[vehicle_id]
    # if user_id not in v.users:
        # raise HTTPException(404, "Vehicle Not Found")

    return vehicles[vehicle_id]

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

# while True: ...


# loop = asyncio.get_event_loop()

# async def check_timers():
#     while True:
#         await asyncio.sleep(1)
#         # print("q")

# loop.create_task(check_timers())
# loop.run_forever()