# Diagrammes de flux de données — SmartPosture

## 1. Diagramme de séquence — Cycle de vie d'une mesure capteur

```mermaid
sequenceDiagram
    actor W as ESP32 / Wokwi
    actor G as Auto-Test Generator
    participant API as FastAPI Backend<br/>(localhost:8000)
    participant P as posture.py
    participant DB as PostgreSQL 16<br/>(sensor_readings)

    note over W,G: Sources de données interchangeables

    alt Simulation Wokwi
        W->>W: Génère données MPU-6050 synthétiques<br/>(archétype posture courant + bruit gaussien)
        W->>API: POST /data<br/>{ accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z }
    else Générateur Python
        G->>G: Sélectionne scénario (60% good / 20% forward<br/>/ 12% side / 8% sudden) + bruit gaussien
        G->>API: POST /data<br/>{ accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z }
    end

    API->>API: Validation Pydantic (SensorDataIn)

    API->>P: detect_posture(data)
    activate P
    P->>P: gyro_norm = √(gx²+gy²+gz²)

    alt gyro_norm > 100 °/s
        P-->>API: sudden_movement (posture_ok=False)
    else |accel_x| > 0.4 g
        P-->>API: forward_lean (posture_ok=False)
    else |accel_y| > 0.4 g
        P-->>API: side_lean (posture_ok=False)
    else
        P-->>API: good (posture_ok=True)
    end
    deactivate P

    API->>DB: INSERT sensor_readings<br/>(timestamp, accel_*, gyro_*, posture_ok, posture_label)
    DB-->>API: reading (avec id auto-généré)

    API-->>W: 200 OK — SensorDataOut (JSON)
```

---

## 2. Diagramme d'architecture — Vue composants

```mermaid
graph TD
    subgraph Embedded["Couche Embarquée (simulée)"]
        ESP[ESP32 DevKit\nWokwi Simulator]
        MPU[MPU-6050\naccel + gyro 6 axes]
        MPU -- I2C SDA/SCL --> ESP
    end

    subgraph Bridge["Tunnel réseau"]
        NGROK[ngrok HTTP tunnel\nWokwi → localhost]
    end

    subgraph Alt["Alternative (sans simulateur)"]
        GEN[generator.py\nPython pur]
    end

    subgraph Backend["Backend (Docker)"]
        API[FastAPI\nmain.py\n:8000]
        POSTURE[posture.py\ndétection règles]
        API --> POSTURE
    end

    subgraph Database["Base de données (Docker)"]
        PG[(PostgreSQL 16\nsensor_readings)]
    end

    subgraph Consult["Consultation"]
        SWAGGER[Swagger UI\n/docs]
        CLIENT[Client HTTP\ncurl / Postman]
    end

    ESP -- WiFi Wokwi-GUEST --> NGROK
    NGROK -- POST /data --> API
    GEN -- POST /data\nlocalhost:8000 --> API
    POSTURE --> API
    API -- SQLAlchemy ORM --> PG
    SWAGGER -- GET /data\nGET /data/stats --> API
    CLIENT -- GET /data\nGET /data/stats --> API
```

---

## 3. Diagramme d'activité — Algorithme de détection de posture

```mermaid
flowchart TD
    START([Réception mesure\nPOST /data]) --> VAL{Validation\nPydantic}

    VAL -->|Invalide| ERR[422 Unprocessable Entity]
    VAL -->|Valide| GYRO

    GYRO["Calcul norme gyroscope\ngyro_norm = √(gx²+gy²+gz²)"]
    GYRO --> C1{gyro_norm\n> 100 °/s ?}

    C1 -->|Oui| SUDDEN[posture_label = sudden_movement\nposture_ok = False\n⚠ Mouvement brusque]
    C1 -->|Non| C2{accel_x\n> 0.4 g ?}

    C2 -->|Oui| FORWARD[posture_label = forward_lean\nposture_ok = False\n⚠ Inclinaison avant/arrière]
    C2 -->|Non| C3{accel_y\n> 0.4 g ?}

    C3 -->|Oui| SIDE[posture_label = side_lean\nposture_ok = False\n⚠ Inclinaison latérale]
    C3 -->|Non| GOOD[posture_label = good\nposture_ok = True\n✓ Posture correcte]

    SUDDEN --> SAVE
    FORWARD --> SAVE
    SIDE --> SAVE
    GOOD --> SAVE

    SAVE[(INSERT\nPostgreSQL)] --> RESP[200 OK\nSensorDataOut JSON]
    RESP --> END([Fin])
```
