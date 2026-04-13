from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Accéléromètre (en g)
    accel_x = Column(Float, nullable=False)
    accel_y = Column(Float, nullable=False)
    accel_z = Column(Float, nullable=False)

    # Gyroscope (en °/s)
    gyro_x = Column(Float, nullable=False)
    gyro_y = Column(Float, nullable=False)
    gyro_z = Column(Float, nullable=False)

    # Résultat de la détection de posture
    posture_ok = Column(Boolean, nullable=False)
    posture_label = Column(String, nullable=False)  # "good", "forward_lean", "side_lean", "sudden_movement"
