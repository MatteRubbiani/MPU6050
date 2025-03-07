/**
 * # Wiring
 * | MPU6050 | MPU6050 |  ESP32  |
 * | ------- | ------- | ------- |
 * | GND     | GND     | GND     |
 * | VCC     | AD0     | 3V3     |
 * | SCL     | SCL     | G22     |
 * | SDA     | SDA     | G21     |
 * 
 * ## ADDR pin 
 * 
 * ADDR low = 0x68 (default)
 * ADDR high = 0x69
 */

#include <WiFi.h>
#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps612.h"

//VARIABLE INITIALIZATION
// Wi-Fi credentials
const char *ssid = "ESP32_WiFi";
const char *password = "12345678";

// Create a server on port 80
WiFiServer server(80);

WiFiClient client;

// initialize the variable to save the number of devices
int device_number;

// initialize the two MPUs with their I2C ID
MPU6050 mpu68(0x68);
MPU6050 mpu69(0x69);

uint8_t error_code = 0U;  // return status after each device operation (0 = success, !0 = error)


// PROTOTYPES
void resetI2C();
int device_count();
void WiFi_initialization(const char *_ssid, const char *_password);
void device_calibration(int _device_number);
void get_quaternions(int _device_number, WiFiClient _client);


// MAIN
void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);

  WiFi_initialization(ssid, password);

  int device_number = device_count();
  Serial.print(device_number);
  device_calibration(device_number);
}

// orientation/motion vars
Quaternion q68;  // [w, x, y, z]         quaternion container
Quaternion q69;  // [w, x, y, z]         quaternion container


void loop() {
  WiFiClient client = server.available();
  if (!client) {
    Serial.println("Client not found");
    delay(1000);
    return;
  }
  while (client.connected()) {
    get_quaternions(device_number, client);
    delay(45);
  }
}


// FUNCTIONS
void resetI2C() {
  Wire.end();    // Termina la comunicazione I²C
  delay(100);    // Aspetta un momento
  Wire.begin();  // Riavvia il bus I²C;
}

int device_count() {
  byte error, address;

  for (address = 1; address < 127; address++) {  // I²C addresses range from 1 to 127
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {  // If no error, a device is found
      device_number++;
    }
  }
  return device_number;
}

void WiFi_initialization(const char *_ssid, const char *_password) {
  // Initialize Wi-Fi as an access point
  WiFi.softAP(_ssid, _password);
  Serial.println("Wi-Fi access point started");
  Serial.println("IP Address: " + WiFi.softAPIP().toString());

  // Start the server
  server.begin();
}

void device_calibration(int _device_number) {
  // device managing
  if (_device_number == 1) {
    // initialize device
    mpu68.initialize();
    error_code = mpu68.dmpInitialize();

    if (error_code == 1U) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: initial memory load failed.\", \"level\": \"ERROR\"}\n");
      while (1) {}
    }
    if (error_code == 2U) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: DMP configuration updates failed.\", \"level\": \"ERROR\"}\n");
      while (1) {}
    }

    // verify connection
    if (!mpu68.testConnection()) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 connection failed.\", \"level\": \"ERROR\"}\n");
    }

    // supply your own gyro offsets here, scaled for min sensitivity
    mpu68.setXGyroOffset(0);
    mpu68.setYGyroOffset(0);
    mpu68.setZGyroOffset(0);
    mpu68.setXAccelOffset(0);
    mpu68.setYAccelOffset(0);
    mpu68.setZAccelOffset(0);

    // Calibration Time: generate offsets and calibrate our MPU6050
    mpu68.CalibrateAccel(20);
    mpu68.CalibrateGyro(20);

    // calibration procedure will dump garbage on serial, we use a newline to fence it
    Serial.print("\n");

    // turn on the DMP, now that it's ready
    mpu68.setDMPEnabled(true);
    //mpu69.setDMPEnabled(true);
  }

  else if (_device_number == 2) {
    // initialize device mpu68
    mpu68.initialize();
    error_code = mpu68.dmpInitialize();

    if (error_code == 1U) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: initial memory load failed.\", \"level\": \"ERROR\"}\n");
      while (1) {}
    }
    if (error_code == 2U) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: DMP configuration updates failed.\", \"level\": \"ERROR\"}\n");
      while (1) {}
    }
    // initialize device mpu69
    mpu69.initialize();
    error_code = mpu69.dmpInitialize();

    if (error_code == 1U) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: initial memory load failed.\", \"level\": \"ERROR\"}\n");
      while (1) {}
    }
    if (error_code == 2U) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 initialization failed: DMP configuration updates failed.\", \"level\": \"ERROR\"}\n");
      while (1) {}
    }

    // verify connection
    if (!mpu68.testConnection()) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x68 connection failed.\", \"level\": \"ERROR\"}\n");
    }

    if (!mpu69.testConnection()) {
      Serial.print("{\"key\": \"/log\", \"value\": \"device 0x69 connection failed.\", \"level\": \"ERROR\"}\n");
    }

    // supply your own gyro offsets here, scaled for min sensitivity
    mpu68.setXGyroOffset(0);
    mpu68.setYGyroOffset(0);
    mpu68.setZGyroOffset(0);
    mpu68.setXAccelOffset(0);
    mpu68.setYAccelOffset(0);
    mpu68.setZAccelOffset(0);

    mpu69.setXGyroOffset(0);
    mpu69.setYGyroOffset(0);
    mpu69.setZGyroOffset(0);
    mpu69.setXAccelOffset(0);
    mpu69.setYAccelOffset(0);
    mpu69.setZAccelOffset(0);

    // Calibration Time: generate offsets and calibrate our MPU6050
    mpu68.CalibrateAccel(20);
    mpu68.CalibrateGyro(20);

    mpu69.CalibrateAccel(20);
    mpu69.CalibrateGyro(20);

    // calibration procedure will dump garbage on serial, we use a newline to fence it
    Serial.print("\n");

    // turn on the DMP, now that it's ready
    mpu68.setDMPEnabled(true);
    mpu69.setDMPEnabled(true);
  }
}

void get_quaternions(int _device_number, WiFiClient _client) {
  if (_device_number == 1) {
    // test the connection before trying to get the data
    while (!mpu68.testConnection()) {
      resetI2C();
    }

    // Get the Latest packet
    uint8_t fifo_buffer68[64];  // FIFO storage buffer
    if (!mpu68.dmpGetCurrentFIFOPacket(fifo_buffer68)) {
      return;
    }
    Quaternion q68;
    mpu68.dmpGetQuaternion(&q68, fifo_buffer68);

    // Get the timestamp
    unsigned long currentTime = millis();

    // // Print the timestamp and quaternions
    String dataToSend = String(currentTime) + ", 1.00, 0.00, 0.00, 0.00" + String(q68.w, 2) + ", " + String(q68.x, 2) + ", " + String(q68.y, 2) + ", " + String(q68.z, 2) + "\n";
    Serial.print(dataToSend);
    _client.print(dataToSend);
  }

  else {
    // test the connection before trying to get the data
    while (!mpu68.testConnection() or !mpu69.testConnection()) {
      resetI2C();
    }

    // Get the Latest packet
    uint8_t fifo_buffer68[64];  // FIFO storage buffer
    if (!mpu68.dmpGetCurrentFIFOPacket(fifo_buffer68)) {
      return;
    }

    uint8_t fifo_buffer69[64];  // FIFO storage buffer
    if (!mpu69.dmpGetCurrentFIFOPacket(fifo_buffer69)) {
      return;
    }

    mpu68.dmpGetQuaternion(&q68, fifo_buffer68);
    mpu69.dmpGetQuaternion(&q69, fifo_buffer69);

    // Get the timestamp
    unsigned long currentTime = millis();

    // Print the timestamp and quaternions
    String dataToSend = String(currentTime) + ", " + String(q68.w, 2) + ", " + String(q68.x, 2) + ", " + String(q68.y, 2) + ", " + String(q68.z, 2) + ", " + String(q69.w, 2) + ", " + String(q69.x, 2) + ", " + String(q69.y, 2) + ", " + String(q69.z, 2) + "\n";
    Serial.print(dataToSend);
    _client.print(dataToSend);
  }
}
