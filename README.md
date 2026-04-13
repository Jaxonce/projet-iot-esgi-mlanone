# SmartPosture / CorpSafe v1

POC d'un gilet intelligent de détection de mauvaise posture en temps réel pour les travailleurs — projet IoT ESGI M2.

---

## Architecture

```
ESP32 (Wokwi simulator)
  └─ génère des données MPU-6050 synthétiques (4 archétypes de posture)
  └─ WiFi "Wokwi-GUEST" → tunnel ngrok
  └─ POST /data → FastAPI (Python 3.12)
        └─ détection posture (règles à seuils)
        └─ PostgreSQL 16 (table sensor_readings)
```

Deux sources de données interchangeables :
- **Simulateur Wokwi** (`wokwi/`) — firmware ESP32 via HTTP et tunnel ngrok
- **Générateur Auto-Test** (`auto_test/generator.py`) — Python pur, sans simulateur

---

## Stack technologique

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| Embarqué (simulé) | ESP32 + PlatformIO + Wokwi | Simulation WiFi réelle, MPU-6050 intégré, accès internet depuis le simulateur |
| Capteur | MPU-6050 (accéléromètre + gyroscope 6 axes) | Standard industrie pour détection de mouvement/posture |
| Tunnel | ngrok (HTTP) | Expose localhost au simulateur cloud Wokwi sans configuration réseau |
| Backend | FastAPI + Python 3.12 | Validation auto avec Pydantic, Swagger UI généré, async natif |
| ORM / BDD | SQLAlchemy + PostgreSQL 16 | Typage fort, migrations futures, fiabilité production |
| Containerisation | Docker Compose | Déploiement reproductible, healthcheck pg_isready |

---

## Diagramme de flux de données

```
┌─────────────────────────────────────────────────────────────────┐
│                      Source de données                          │
│                                                                 │
│  [ESP32 / Wokwi]          [Auto-Test generator.py]             │
│  MPU-6050 synthétique      Python pur, 4 scénarios             │
│  WiFi Wokwi-GUEST          distribution 60/20/12/8%            │
│        │                          │                            │
│        └──────── HTTP POST ────────┘                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   POST /data            │
              │   FastAPI backend       │
              │   localhost:8000        │
              │                         │
              │  1. Validation Pydantic  │
              │  2. detect_posture()    │
              │     ├─ gyro_norm>100    │ → sudden_movement
              │     ├─ |accel_x|>0.4g  │ → forward_lean
              │     ├─ |accel_y|>0.4g  │ → side_lean
              │     └─ sinon           │ → good
              │  3. INSERT PostgreSQL   │
              └─────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   PostgreSQL 16         │
              │   table sensor_readings │
              │                         │
              │  id, timestamp          │
              │  accel_x/y/z (g)        │
              │  gyro_x/y/z (°/s)       │
              │  posture_ok (bool)      │
              │  posture_label (string) │
              └─────────────────────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼                            ▼
     GET /data?limit=50          GET /data/stats
     dernières mesures           taux bonnes/mauvaises
```

---

## Placement du capteur sur le gilet

```
        [dos du travailleur]

        ┌────────────────┐
        │                │
        │   ┌────────┐   │
        │   │MPU-6050│   │  ← capteur centré, entre les omoplates
        │   │   ★    │   │    axe Z vertical (vers le haut)
        │   └────────┘   │    posture droite : accel_z ≈ 1g
        │                │                    accel_x ≈ 0
        │     GILET      │                    accel_y ≈ 0
        │                │
        └────────────────┘

  Inclinaison avant  → accel_x ↑  (>0.4g = alerte)
  Inclinaison latérale → accel_y ↑ (>0.4g = alerte)
  Mouvement brusque  → gyro_norm ↑ (>100°/s = alerte)
```

---

## Prérequis

- Docker Desktop
- Python 3.10+ (pour auto_test uniquement)
- VS Code + extensions PlatformIO + Wokwi (pour simulation ESP32)
- Compte ngrok (pour relier Wokwi au backend)

---

## Installation et démarrage

### 1. Démarrer le backend (Docker)

```bash
docker-compose up --build
```

Le backend est accessible sur http://localhost:8000  
Swagger UI : http://localhost:8000/docs

### 2. Lancer le générateur Auto-Test

```bash
cd auto_test
pip install requests
python generator.py                      # scénario aléatoire en boucle (60% good)
python generator.py --scenario forward   # inclinaison avant uniquement
python generator.py --scenario side      # inclinaison latérale uniquement
python generator.py --scenario sudden    # mouvement brusque uniquement
python generator.py --count 20           # 20 mesures puis stop
python generator.py --interval 2.0       # une mesure toutes les 2 secondes
```

### 3. Simulation ESP32 via Wokwi (optionnel)

> Nécessite un tunnel ngrok actif pointant vers localhost:8000

```bash
# Terminal 1 : démarrer ngrok
ngrok http 8000

# Mettre à jour l'URL dans wokwi/smartposture.ino :
# const char* BACKEND_URL = "https://<votre-id>.ngrok-free.app/data";

# Terminal 2 : compiler le firmware
cd wokwi && pio run

# VS Code : Cmd+Shift+P → "Wokwi: Start Simulator"
```

> **Note** : la licence Wokwi gratuite est nécessaire pour la simulation WiFi.  
> `F1` → "Wokwi: Request a Free License"

---

## API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/data` | Envoyer une mesure capteur (JSON) |
| GET | `/data?limit=50` | Récupérer les dernières mesures |
| GET | `/data/stats` | Taux de bonnes/mauvaises postures |
| GET | `/health` | Santé de l'API |
| GET | `/docs` | Swagger UI auto-généré |

### Exemple de payload POST /data

```json
{
  "accel_x": 0.55,
  "accel_y": 0.01,
  "accel_z": 0.85,
  "gyro_x": 0.5,
  "gyro_y": 1.2,
  "gyro_z": -0.3
}
```

### Exemple de réponse GET /data/stats

```json
{
  "total": 120,
  "good_posture": 73,
  "bad_posture": 47,
  "bad_posture_rate": 39.2
}
```

---

## Logique de détection de posture

Implémentée dans `backend/posture.py`. Évaluation par priorité :

1. **sudden_movement** — norme gyroscope > 100 °/s → risque TMS élevé
2. **forward_lean** — `|accel_x|` > 0.4 g → inclinaison avant/arrière
3. **side_lean** — `|accel_y|` > 0.4 g → inclinaison latérale
4. **good** — sinon → posture correcte

---

## Structure du projet

```
PROJECT_IOT/
├── backend/
│   ├── main.py          # API FastAPI (4 endpoints)
│   ├── posture.py       # Algorithme de détection
│   ├── models.py        # Modèle SQLAlchemy
│   ├── schemas.py       # Schémas Pydantic
│   ├── database.py      # Connexion PostgreSQL
│   ├── requirements.txt
│   └── Dockerfile
├── auto_test/
│   └── generator.py     # Générateur de données synthétiques
├── wokwi/
│   ├── smartposture.ino # Firmware ESP32 (Arduino)
│   ├── diagram.json     # Schéma de câblage Wokwi
│   ├── platformio.ini   # Config PlatformIO
│   └── wokwi.toml       # Config extension Wokwi VS Code
├── docker-compose.yml
└── README.md
```

---

## Auteur

Projet ESGI M2 — SafeWear Technologies POC
