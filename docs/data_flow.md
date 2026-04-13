# Diagramme de flux de données — SmartPosture

```mermaid
flowchart LR
    ESP["ESP32 / Wokwi"] --> NGROK["Cloudflare Tunnel\nhttps://xxx.trycloudflare.com"]
    GEN["Auto-Test\ngenerator.py"] --> API

    NGROK --> API["FastAPI Backend\n(:8000)"]
    API --> DB[("PostgreSQL\n(:5432)")]
```
