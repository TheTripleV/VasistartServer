from typing import Optional, Tuple
from pydantic import BaseModel
import enum

class VehicleType(enum.Enum):
    CAR = 0
    MOTORCYCLE = 1

class VehicleFeatures(BaseModel):
    temperature: bool = True
    front_defrost: bool = True
    rear_defrost: bool = True
    lock: bool = True
    location: bool = True
    engine: bool = True

class VehicleState(BaseModel):
    temperature: float = 70
    front_defrost_on: bool = False
    rear_defrost_on: bool = False
    locked: bool = False
    engine_on: bool = False
    engine_on_desired: bool = False
    location: Optional[Tuple[float, float]] = None
    notif_loc: bool = True
    notif_unlock_delay = -1
    
class VehicleAccessLevel(enum.Enum):
    BASIC = 0
    ADMIN = 1

class VehicleUser(BaseModel):
    id: str
    access_level: VehicleAccessLevel

class Vehicle(BaseModel):
    name: str = ""
    users: list[VehicleUser] = []
    type: VehicleType = VehicleType.CAR
    features: VehicleFeatures = VehicleFeatures()
    state: VehicleState = VehicleState()