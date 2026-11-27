#include <ESP32Servo.h>
#include <DFRobot_TFmini.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// El ESP32 tiene Serial2 por hardware en los pines 16 y 17 
#define RXD2 17 // Conectar al TX (Verde) del TFmini
#define TXD2 16 // Conectar al RX (Azul) del TFmini

#define PIN_SERVO_AZ 18
#define PIN_SERVO_LA 19

DFRobot_TFmini TFmini;
Servo MOTOR_AZ;
Servo MOTOR_LA;


int status = WL_IDLE_STATUS; 
//-----------------------Credenciales de Wifi -------------------

const char *NAME = "sagemcomDF20";
const char *PASS = "EDUZNU2N2CDNJN"; 

//---------------------------------------------------------------

//-----------------------Credenciales de MQTT -------------------
const char* MQTT_SERVER = "192.168.0.27";
const int MQTT_PORT = 1883;
const char* MQTT_USER = "";
const char* MQTT_PASSWORD = "";
const char* MQTT_TOPIC = "Lidar/Distance";
//---------------------------------------------------------------

WiFiClient espClient;
PubSubClient client(espClient);

JsonDocument doc;

uint16_t  distanceT;

void wifiSetup();
void mqttSetup();
void servoSetup();

void setup() {
  Serial.begin(115200);
  Serial.println("Iniciando");

  wifiSetup();
  mqttSetup();
  servoSetup();

  Serial2.begin(115200, SERIAL_8N1, RXD2, TXD2);
  TFmini.begin(Serial2);//Problema aqui
  Serial.println("Iniciando");
  delay(1000);


}

void loop() {
  client.loop();

  //
  
  for(uint8_t j = 0; j <= 180;j++){
  Serial.println("for1");
  MOTOR_AZ.write(j);
    doc["theta"] = j;
    JsonArray distances = doc["distances"].to<JsonArray>();
    
    if(j%2 == 0){ 
      for(uint8_t i = 0; i <= 180; i++){
        client.loop();
        Serial.println("for2");
        MOTOR_LA.write(i);
        
        if(TFmini.measure()){  
          Serial.println("MEDIDA");                    //Measure Distance and get signal strength
          distanceT = TFmini.getDistance();
          distances.add(distanceT);        //Get distance data
          Serial.print("Distance = ");
          Serial.print(distanceT);
          Serial.println("cm");
       }

      }
   }else{
    for(uint8_t i = 181; i > 0; i--){
        client.loop();
        Serial.println("for3");
        MOTOR_LA.write(i);
        if(TFmini.measure()){                                
          distanceT = TFmini.getDistance();//Measure Distance
          distances.add(distanceT);     
          Serial.print("Distance = ");
          Serial.print(distanceT);
          Serial.println("cm"); 
        }
        
      } 
    }
    char buffer[1024];
    size_t n = serializeJson(doc, buffer);
    client.publish(MQTT_TOPIC, buffer, n);
  }
}


 void wifiSetup(){
  WiFi.mode(WIFI_STA);
  WiFi.begin(NAME, PASS);
  while(status != WL_CONNECTED){
    Serial.println("Conectando wifi");
    delay(500);
    status = WiFi.status();
  }
  Serial.print("WiFi conectado. IP del ESP32: ");
}

void mqttSetup(){
  client.setClient(espClient);
  client.setServer(MQTT_SERVER, MQTT_PORT);
  while (!client.connected()){
      Serial.println("Conectando MQTT...");
      if (client.connect("espClient_lidar", MQTT_USER, MQTT_PASSWORD)) {
        Serial.println("Conectado a MQTT");
      } else {
        Serial.print("Error al conectar a MQTT, rc=");
        Serial.print(client.state());
        delay(2000);
      }
  }
    client.setBufferSize(1024); 
}

void servoSetup(){
  // Configuración obligatoria para la librería ESP32Servo actual
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);

  MOTOR_AZ.setPeriodHertz(50);
  MOTOR_LA.setPeriodHertz(50);

  MOTOR_AZ.attach(PIN_SERVO_AZ, 500, 2400);
  MOTOR_LA.attach(PIN_SERVO_LA, 500, 2400);
}