from datetime import datetime
from pydantic import BaseModel


class SensorDataIn(BaseModel):
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float


class SensorDataOut(BaseModel):
    id: int
    timestamp: datetime
    accel_x: float
    accel_y: float
    accel_z: float
    gyro_x: float
    gyro_y: float
    gyro_z: float
    posture_ok: bool
    posture_label: str

    model_config = {"from_attributes": True}


class PostureResult(BaseModel):
    posture_ok: bool
    posture_label: str
    message: str
