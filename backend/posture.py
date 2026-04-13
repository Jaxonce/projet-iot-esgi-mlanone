"""
Algorithme de détection de posture basé sur les données MPU-6050.

Référentiel : capteur placé dans le dos du gilet (colonne vertébrale).
Posture droite : accel_z ≈ 1g, accel_x ≈ 0, accel_y ≈ 0
"""

import math
from schemas import SensorDataIn, PostureResult

# Seuils de détection (ajustables)
FORWARD_LEAN_THRESHOLD = 0.4    # inclinaison avant/arrière (accel_x) en g
SIDE_LEAN_THRESHOLD = 0.4       # inclinaison latérale (accel_y) en g
SUDDEN_MOVEMENT_THRESHOLD = 100  # mouvement brusque (gyro norm) en °/s


def detect_posture(data: SensorDataIn) -> PostureResult:
    gyro_norm = math.sqrt(data.gyro_x**2 + data.gyro_y**2 + data.gyro_z**2)

    if gyro_norm > SUDDEN_MOVEMENT_THRESHOLD:
        return PostureResult(
            posture_ok=False,
            posture_label="sudden_movement",
            message="Mouvement brusque détecté — risque de TMS élevé"
        )

    if abs(data.accel_x) > FORWARD_LEAN_THRESHOLD:
        direction = "avant" if data.accel_x > 0 else "arrière"
        return PostureResult(
            posture_ok=False,
            posture_label="forward_lean",
            message=f"Inclinaison vers l'{direction} trop importante"
        )

    if abs(data.accel_y) > SIDE_LEAN_THRESHOLD:
        direction = "gauche" if data.accel_y > 0 else "droite"
        return PostureResult(
            posture_ok=False,
            posture_label="side_lean",
            message=f"Inclinaison latérale vers la {direction} trop importante"
        )

    return PostureResult(
        posture_ok=True,
        posture_label="good",
        message="Posture correcte"
    )
