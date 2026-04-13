from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import engine, get_db, Base
from models import SensorReading
from schemas import SensorDataIn, SensorDataOut
from posture import detect_posture

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmartPosture API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/data", response_model=SensorDataOut)
def receive_sensor_data(data: SensorDataIn, db: Session = Depends(get_db)):
    """Reçoit une mesure du capteur MPU-6050 et détecte la posture."""
    result = detect_posture(data)

    reading = SensorReading(
        accel_x=data.accel_x,
        accel_y=data.accel_y,
        accel_z=data.accel_z,
        gyro_x=data.gyro_x,
        gyro_y=data.gyro_y,
        gyro_z=data.gyro_z,
        posture_ok=result.posture_ok,
        posture_label=result.posture_label,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@app.get("/data", response_model=List[SensorDataOut])
def get_readings(limit: int = 50, db: Session = Depends(get_db)):
    """Retourne les dernières mesures stockées."""
    return db.query(SensorReading).order_by(SensorReading.timestamp.desc()).limit(limit).all()


@app.get("/data/stats")
def get_stats(db: Session = Depends(get_db)):
    """Statistiques globales : nombre de mauvaises postures vs bonnes."""
    total = db.query(SensorReading).count()
    bad = db.query(SensorReading).filter(SensorReading.posture_ok == False).count()
    good = total - bad
    return {
        "total": total,
        "good_posture": good,
        "bad_posture": bad,
        "bad_posture_rate": round(bad / total * 100, 1) if total > 0 else 0,
    }
