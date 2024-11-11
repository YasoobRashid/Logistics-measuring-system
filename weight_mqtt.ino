#include <Wire.h>
#include <HX711.h>
#include <WiFiNINA.h>
#include <ArduinoMqttClient.h>

// WiFi credentials
const char* ssid = "realme X2";
const char* password = "yasoob88";

// MQTT settings
const char* mqtt_broker = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* topic = "device/weight";

// HX711 setup for weight
#define LOADCELL_DOUT_PIN 4
#define LOADCELL_SCK_PIN 5
HX711 scale;

// WiFi and MQTT client objects
WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

void setup() {
  Serial.begin(115200);

  // Initialize WiFi
  connectWiFi();

  // Initialize MQTT
  connectMQTT();

  // Initialize HX711 for weight measurement with calibration
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_offset(4294798238); 
  scale.set_scale(593.024292);  
  
  Serial.println("Scale initialized with new calibration values.");
}

void connectWiFi() {
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi");
}

void connectMQTT() {
  Serial.print("Connecting to MQTT broker...");
  while (!mqttClient.connect(mqtt_broker, mqtt_port)) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConnected to MQTT broker");
}

void loop() {
  // Poll the MQTT client to maintain connection
  mqttClient.poll();

  // Read weight with averaging for stability
  float weight = scale.get_units(20); // Average 20 readings
  if (weight < 0) {
    weight = 0; // Ensure no negative weights are reported
  }

  // Publish weight data to MQTT
  char message[50];
  snprintf(message, sizeof(message), "Weight: %.2f g", weight);

  Serial.print("Publishing: ");
  Serial.println(message);

  mqttClient.beginMessage(topic);
  mqttClient.print(message);
  mqttClient.endMessage();

  delay(1000); // Delay between transmissions
}
