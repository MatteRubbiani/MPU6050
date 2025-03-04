#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>  // Required for notifications
#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps612.h"


// BLE VARIABLES & CONSTANTS//

// UUIDs for Service & Characteristic (Must match Python script)
#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

// Callback for device connection
class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer *pServer) {
    deviceConnected = true;
    Serial.println("✅ Device connected!");
  }

  void onDisconnect(BLEServer *pServer) {
    deviceConnected = false;
    Serial.println("🔴 Device disconnected...");
    BLEDevice::startAdvertising();  // Restart advertising
  }
};

// SENSORS VARIABLES & CONSTANTS //

#define MPU6050_ADDR_68 0x68  // I2C address of MPU6050
#define ACCEL_XOUT_H 0x3B     // First register of accelerometer data
#define PWR_MGMT_1 0x6B       // Power management register

// Constants to convert acceleration
float ACCEL_SCALE = 16384.0;
float GRAVITY = 9.81;

// MPUs with their I2C ID
MPU6050 mpu68(MPU6050_ADDR_68);

// Other variables
int device_number;
int loop_number;
int const_values_number;
bool initial_gravity_ok = false;
String message;

// MAIN
void setup() {
  Serial.begin(115200);
  BLE_setup();
  Wire.begin();
  Wire.setClock(100000);
  delay(1000);

  device_number = device_count();
  set_MPU6050();

  while (!initial_gravity_ok) {
    message = get_initial_acceleration();
    if (message != "error") {
      initial_gravity_ok = true;
    }
  }  

  device_calibration();
}

void loop() {
  if (deviceConnected) {
    if (loop_number != 0) {
      message = get_quaternion_and_acceleration();
    }
    loop_number++;

    pCharacteristic->setValue(message.c_str());
    pCharacteristic->notify();  // ✅ Send notification
    Serial.println("📤 Sent: " + message);
  }

  delay(50);
}

// FUNCTIONS
void BLE_setup() {
  // Initialize BLE
  Serial.println("🔵 Starting BLE...");
  BLEDevice::init("Long name works now");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create Characteristic with NOTIFY property
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);

  // Required for notifications to work
  pCharacteristic->addDescriptor(new BLE2902());

  // Start Service
  pService->start();

  // Start Advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->start();

  Serial.println("📡 BLE Advertising...");

  // Initialize sensor
  Wire.begin();
  Wire.setClock(100000);
  delay(5000);
}

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

void set_MPU6050() {
  // Wake up MPU6050 (it starts in sleep mode)
  Wire.beginTransmission(MPU6050_ADDR_68);
  Wire.write(PWR_MGMT_1);
  Wire.write(0x00);  // Clear sleep mode
  Wire.endTransmission();
}

String get_initial_acceleration() {
  // raw accelerations
  int16_t _ax68, _ay68, _az68;

  // raw accelerations in m/s^2
  float _gx68, _gy68, _gz68;

  Wire.beginTransmission(MPU6050_ADDR_68);
  Wire.write(ACCEL_XOUT_H);  // Start reading from ACCEL_XOUT_H
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_ADDR_68, 6, true);  // Request 6 bytes

  _ax68 = (Wire.read() << 8) | Wire.read();  // X-axis
  _ay68 = (Wire.read() << 8) | Wire.read();  // Y-axis
  _az68 = (Wire.read() << 8) | Wire.read();  // Z-axis

  _gx68 = _ax68 / ACCEL_SCALE * GRAVITY;
  _gy68 = _ay68 / ACCEL_SCALE * GRAVITY;
  _gz68 = _az68 / ACCEL_SCALE * GRAVITY;

  if (_gx68 != 0 && _gy68 != 0 && _gz68 != 0) {
    String dataToSend = "*, " + 
                      String(_gx68) + ", " +
                      String(_gy68) + ", " +
                      String(_gz68) + "\n ";
    delay(500);
    return dataToSend;
  }

  else {
    return "error";
  }
}

void device_calibration() {
  // Error state variable (0 = success, !0 = error)
  uint8_t error_code = 0U;

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
}

bool are_quaternions_equal(Quaternion q1, Quaternion q2, float epsilon = 0.01) {
    return (fabs(q1.w - q2.w) < epsilon &&
            fabs(q1.x - q2.x) < epsilon &&
            fabs(q1.y - q2.y) < epsilon &&
            fabs(q1.z - q2.z) < epsilon);
}

String get_quaternion_and_acceleration() {
  // FIFO storage buffers
  uint8_t fifo_buffer68[64];  // FIFO storage buffer

  // Orientation/motion vars for successive motion elaboration
  Quaternion q68;  // [w, x, y, z]
  Quaternion last_q68;
  Quaternion q69;  // [w, x, y, z]
  Quaternion last_q69;
  VectorInt16 a68;        // [x, y, z]
  VectorInt16 a69;        // [x, y, z]
  VectorInt16 aReal68;    // [x, y, z]
  VectorInt16 aReal69;    // [x, y, z]
  VectorFloat gravity68;  // [x, y, z]
  VectorFloat gravity69;  // [x, y, z]

  // test the connection before trying to get the data
  while (!mpu68.testConnection()) {
    resetI2C();
  }

  // Get the Latest packet 
  if (!mpu68.dmpGetCurrentFIFOPacket(fifo_buffer68)) {
    return "#-, data corrupted in buffer\n";
  }

  mpu68.dmpGetQuaternion(&q68, fifo_buffer68);
  mpu68.dmpGetAccel(&a68, fifo_buffer68);
  mpu68.dmpGetGravity(&gravity68, &q68);
  mpu68.dmpGetLinearAccel(&aReal68, &a68, &gravity68);

  // Get the timestamp
  unsigned long currentTime = millis();

  // Convert acceleration into multiples of g
  float ax = aReal68.x / ACCEL_SCALE * GRAVITY;
  float ay = aReal68.y / ACCEL_SCALE * GRAVITY;
  float az = aReal68.z / ACCEL_SCALE * GRAVITY;

  // Print the timestamp and quaternions
  String dataToSend = "#, " + 
                      String(currentTime) + ", " + 
                      String(q68.w, 2) + ", " + 
                      String(q68.x, 2) + ", " + 
                      String(q68.y, 2) + ", " + 
                      String(q68.z, 2) + ", " +
                      String(ax) + ", " +
                      String(ay) + ", " +
                      String(az) + "\n ";

  delay(50);
  return dataToSend;
}


  
  

