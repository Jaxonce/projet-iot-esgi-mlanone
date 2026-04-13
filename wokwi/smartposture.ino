#include <WiFi.h>
#include <HTTPClient.h>
#include <Arduino.h>

const char* WIFI_SSID     = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

const char* BACKEND_URL = "https://evidence-send-watches-fully.trycloudflare.com/data";

#define INTERVAL_MS 1000

#define POSTURE_GOOD    0
#define POSTURE_FORWARD 1
#define POSTURE_SIDE    2
#define POSTURE_SUDDEN  3

int currentPosture   = POSTURE_GOOD;
int postureCounter   = 0;
int postureDuration  = 10;

float gaussNoise(float mean, float stddev) {
  float u = 0;
  for (int i = 0; i < 3; i++) u += (float)random(-1000, 1000) / 1000.0;
  return mean + u * stddev;
}

void connectWifi() {
  Serial.print("Connexion WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connecté — IP : " + WiFi.localIP().toString());
}

void setup() {
  Serial.begin(115200);

  Serial.println("=== SmartPosture boot ===");
  randomSeed(analogRead(0));
  connectWifi();
}

void loop() {
  float ax, ay, az, gx, gy, gz;

  postureCounter++;
  if (postureCounter >= postureDuration) {
    postureCounter  = 0;
    postureDuration = 8 + random(0, 12);
    int r = random(0, 100);
    if      (r < 60) currentPosture = POSTURE_GOOD;
    else if (r < 80) currentPosture = POSTURE_FORWARD;
    else if (r < 92) currentPosture = POSTURE_SIDE;
    else             currentPosture = POSTURE_SUDDEN;
  }

  switch (currentPosture) {
    case POSTURE_GOOD:
      ax = gaussNoise(0.0, 0.05); ay = gaussNoise(0.0, 0.05); az = gaussNoise(1.0, 0.05);
      gx = gaussNoise(0.0, 2.0);  gy = gaussNoise(0.0, 2.0);  gz = gaussNoise(0.0, 2.0);
      break;
    case POSTURE_FORWARD:
      ax = gaussNoise(0.55, 0.05); ay = gaussNoise(0.0,  0.05); az = gaussNoise(0.85, 0.05);
      gx = gaussNoise(0.0,  3.0);  gy = gaussNoise(0.0,  3.0);  gz = gaussNoise(0.0,  3.0);
      break;
    case POSTURE_SIDE:
      ax = gaussNoise(0.0,  0.05); ay = gaussNoise(0.5,  0.05); az = gaussNoise(0.87, 0.05);
      gx = gaussNoise(0.0,  3.0);  gy = gaussNoise(0.0,  3.0);  gz = gaussNoise(0.0,  3.0);
      break;
    case POSTURE_SUDDEN:
      ax = gaussNoise(0.0, 0.2); ay = gaussNoise(0.0, 0.2);   az = gaussNoise(1.0,  0.2);
      gx = gaussNoise(0.0, 50.0); gy = gaussNoise(130.0, 15.0); gz = gaussNoise(0.0, 20.0);
      break;
  }

  // Construction du JSON
  String payload = "{";
  payload += "\"accel_x\":" + String(ax, 3) + ",";
  payload += "\"accel_y\":" + String(ay, 3) + ",";
  payload += "\"accel_z\":" + String(az, 3) + ",";
  payload += "\"gyro_x\":"  + String(gx, 3) + ",";
  payload += "\"gyro_y\":"  + String(gy, 3) + ",";
  payload += "\"gyro_z\":"  + String(gz, 3);
  payload += "}";

  Serial.println("Envoi : " + payload);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(BACKEND_URL);
    http.addHeader("Content-Type", "application/json");
    http.addHeader("ngrok-skip-browser-warning", "true");

    int httpCode = http.POST(payload);

    if (httpCode == 200) {
      String response = http.getString();
      Serial.println("Réponse : " + response);
    } else {
      Serial.println("Erreur HTTP : " + String(httpCode));
    }
    http.end();
  } else {
    Serial.println("WiFi perdu, reconnexion...");
    connectWifi();
  }

  delay(INTERVAL_MS);
}
