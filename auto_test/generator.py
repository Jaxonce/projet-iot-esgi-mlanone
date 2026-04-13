"""
Auto-Test Generator — SmartPosture
Simule des données MPU-6050 réalistes et les envoie au backend FastAPI.

Usage:
    python generator.py                  # scénario aléatoire en boucle
    python generator.py --scenario bad   # uniquement mauvaises postures
    python generator.py --interval 1.0   # 1 mesure par seconde
"""

import argparse
import time
import random
import math
import requests

BACKEND_URL = "http://localhost:8000/data"


def generate_good_posture() -> dict:
    """Posture droite : accel_z ≈ 1g, accel_x/y ≈ 0, gyro faible."""
    return {
        "accel_x": random.gauss(0.0, 0.05),
        "accel_y": random.gauss(0.0, 0.05),
        "accel_z": random.gauss(1.0, 0.05),
        "gyro_x": random.gauss(0.0, 2.0),
        "gyro_y": random.gauss(0.0, 2.0),
        "gyro_z": random.gauss(0.0, 2.0),
    }


def generate_forward_lean() -> dict:
    """Inclinaison vers l'avant : accel_x augmente."""
    return {
        "accel_x": random.gauss(0.55, 0.05),
        "accel_y": random.gauss(0.0, 0.05),
        "accel_z": random.gauss(0.85, 0.05),
        "gyro_x": random.gauss(0.0, 3.0),
        "gyro_y": random.gauss(0.0, 3.0),
        "gyro_z": random.gauss(0.0, 3.0),
    }


def generate_side_lean() -> dict:
    """Inclinaison latérale : accel_y augmente."""
    return {
        "accel_x": random.gauss(0.0, 0.05),
        "accel_y": random.gauss(0.5, 0.05),
        "accel_z": random.gauss(0.87, 0.05),
        "gyro_x": random.gauss(0.0, 3.0),
        "gyro_y": random.gauss(0.0, 3.0),
        "gyro_z": random.gauss(0.0, 3.0),
    }


def generate_sudden_movement() -> dict:
    """Mouvement brusque : norme gyro élevée."""
    angle = random.uniform(0, 2 * math.pi)
    intensity = random.gauss(130, 15)
    return {
        "accel_x": random.gauss(0.0, 0.2),
        "accel_y": random.gauss(0.0, 0.2),
        "accel_z": random.gauss(1.0, 0.2),
        "gyro_x": intensity * math.cos(angle),
        "gyro_y": intensity * math.sin(angle),
        "gyro_z": random.gauss(0.0, 20.0),
    }


SCENARIOS = {
    "good": generate_good_posture,
    "forward": generate_forward_lean,
    "side": generate_side_lean,
    "sudden": generate_sudden_movement,
}

# Distribution réaliste : 60% bonne posture, 40% mauvaise
RANDOM_WEIGHTS = [
    ("good", 0.60),
    ("forward", 0.20),
    ("side", 0.12),
    ("sudden", 0.08),
]


def pick_random_scenario() -> str:
    r = random.random()
    cumul = 0.0
    for name, weight in RANDOM_WEIGHTS:
        cumul += weight
        if r < cumul:
            return name
    return "good"


def send(data: dict) -> None:
    try:
        resp = requests.post(BACKEND_URL, json=data, timeout=3)
        resp.raise_for_status()
        result = resp.json()
        status = "OK" if result["posture_ok"] else f"ALERTE ({result['posture_label']})"
        print(f"[{result['timestamp']}] {status} | accel=({data['accel_x']:.2f}, {data['accel_y']:.2f}, {data['accel_z']:.2f})")
    except requests.exceptions.ConnectionError:
        print("Erreur : impossible de joindre le backend. Est-il démarré ?")
    except Exception as e:
        print(f"Erreur : {e}")


def main():
    parser = argparse.ArgumentParser(description="SmartPosture Auto-Test Generator")
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()) + ["random"], default="random")
    parser.add_argument("--interval", type=float, default=0.5, help="Secondes entre chaque mesure")
    parser.add_argument("--count", type=int, default=0, help="Nombre de mesures (0 = infini)")
    args = parser.parse_args()

    print(f"Démarrage du générateur | scénario={args.scenario} | intervalle={args.interval}s")
    print(f"Backend : {BACKEND_URL}\n")

    sent = 0
    try:
        while True:
            scenario = args.scenario if args.scenario != "random" else pick_random_scenario()
            data = SCENARIOS[scenario]()
            send(data)
            sent += 1
            if args.count > 0 and sent >= args.count:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nArrêt. {sent} mesures envoyées.")


if __name__ == "__main__":
    main()
