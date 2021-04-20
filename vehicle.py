from typing import Optional, Tuple
from pydantic import BaseModel
import enum

class VehicleType(enum.Enum):
    CAR = "CAR"
    MOTORCYCLE = "MOTORCYCLE"

class VehicleFeatures(BaseModel):
    temperature: bool = True
    front_defrost: bool = True
    rear_defrost: bool = True
    lock: bool = True
    location: bool = True
    engine: bool = True

class Location(BaseModel):
    latitude: float = 0
    longitude: float = 0

class FanSpeed(enum.Enum):
    OFF = "OFF"
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"
    AUTO = "AUTO"
class VehicleState(BaseModel):
    temperature: float = 70
    front_defrost_on: bool = False
    rear_defrost_on: bool = False
    ac_on: bool = False
    ac_fan_speed: FanSpeed = FanSpeed.OFF
    locked: bool = False
    engine_on: bool = False
    engine_on_desired: bool = False
    location: Location = Location()
    notif_loc: bool = True
    notif_unlock_delay = -1
    
class Vehicle(BaseModel):
    name: str = "noname"
    id: str = "noid"
    type: VehicleType = VehicleType.CAR
    features: VehicleFeatures = VehicleFeatures()
    state: VehicleState = VehicleState()