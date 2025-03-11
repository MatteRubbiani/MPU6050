#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h> 
#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps612.h"
#include "SPIFFS.h"

// LED VARIABLES & CONSTANTS //
#define LED_PIN 27  // Definisce il pin del LED


// BUTTON VARIABLES & CONSTANTS //
#define BUTTON_PIN 26  // Bottone collegato al pin 26

unsigned long button_press_start = 0;  // Tempo di inizio pressione
unsigned long button_press_duration = 0;  // Durata della pressione 
bool button_state = false;  // Stato corrente del bottone (premuto o non premuto)
bool last_button_state = false;
bool perform_measurement = false;


// BLE VARIABLES & CONSTANTS //
#define SERVICE_UUID "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define NOTIFY_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
#define COMMAND_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a9"

BLECharacteristic *pCharacteristic;
BLECharacteristic *pCommandCharacteristic;
bool deviceConnected = false;
String cmd = "None";
String file_name;

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

// Callback for command reception
class CommandCallbacks : public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
    cmd = pCharacteristic->getValue();
    Serial.print("Received command: ");
    Serial.println(cmd.c_str());
  }
};


// SENSORS VARIABLES & CONSTANTS //
#define MPU6050_ADDR_68 0x68  // I2C address of MPU6050
#define ACCEL_XOUT_H 0x3B     // First register of accelerometer data
#define PWR_MGMT_1 0x6B       // Power management register

// Constants to convert acceleration
float ACCEL_SCALE = 16384.0;
float GRAVITY = 9.81;

// MPU with its I2C ID
MPU6050 mpu68(MPU6050_ADDR_68);

// Other variables
int loop_number;
int counter = 0;
int const_values_number;
bool initial_gravity_ok = false;
String initial_gravity;
String message;

// MAIN
void setup() {
  Serial.begin(115200);
  digitalWrite(LED_PIN, HIGH);
  BLE_setup();
  SPIFFS_setup();
  Wire.begin();
  Wire.setClock(100000);
  delay(1000);
  pinMode(BUTTON_PIN, INPUT_PULLUP);  
  pinMode(LED_PIN, OUTPUT);
  set_MPU6050();
  check_initial_gravity(initial_gravity_ok);
  device_calibration();
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  button_state = digitalRead(BUTTON_PIN) == LOW;  // Il bottone è attivo LOW

  // Se il bottone è appena stato premuto
  if (button_state && !last_button_state) {
    button_press_start = millis();  // Inizia a contare il tempo di pressione
  }

  // Se il bottone è rilasciato e la durata della pressione è stata misurata
  if (!button_state && last_button_state) {
    button_press_duration = millis() - button_press_start;  // Calcola la durata della pressione

    if (button_press_duration < 5000) {
      if (perform_measurement) {
        perform_measurement = false;
        digitalWrite(LED_PIN, LOW);
      }
      else {
        perform_measurement = true;
        file_name = get_next_file_name();
      }
    }

    else {
      Serial.println("Resetting ESP32 ...");
      digitalWrite(LED_PIN, HIGH);
      delay(1000);
      //clear_memory(); 
      ESP.restart();  // Perform software reset
    }
  }

  if (perform_measurement == true) {
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    if (loop_number == 0) {
    message = initial_gravity;
    } 
    else {
      message = get_quaternion_and_acceleration();
    }
    loop_number++;

    if (deviceConnected) {
      handle_command();
    }   

    else {
      cmd = "None";
      write_file(file_name, message);
      Serial.println("Saved in " + file_name + ": " + message);
    }
  }

  last_button_state = button_state;
  delay(50);
}

// FUNCTIONS
void BLE_setup() {
  // Initialize BLE
  Serial.println("🔵 Starting BLE...");
  BLEDevice::init("ESP32_1");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create Characteristic with NOTIFY property
  pCharacteristic = pService->createCharacteristic(
    NOTIFY_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY);

  // Required for notifications to work
  pCharacteristic->addDescriptor(new BLE2902());

  // Create the command characteristic for writes
  pCommandCharacteristic = pService->createCharacteristic(
    COMMAND_UUID,
    BLECharacteristic::PROPERTY_WRITE| BLECharacteristic::PROPERTY_NOTIFY);
  pCommandCharacteristic->setCallbacks(new CommandCallbacks());

  // Start Service
  pService->start();

  // Start Advertising
  BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->start();

  Serial.println("📡 BLE Advertising...");
}

void SPIFFS_setup() {
  if (!SPIFFS.begin(true)) {  // true = format if mount fails
        Serial.println("SPIFFS Mount Failed");
        return;
    }

  Serial.println("SPIFFS Mounted Successfully");
}

void reset_I2C() {
  Wire.end();    // Termina la comunicazione I²C
  delay(100);    // Aspetta un momento
  Wire.begin();  // Riavvia il bus I²C;
}

void set_MPU6050() {
  // Wake up MPU6050 (it starts in sleep mode)
  Wire.beginTransmission(MPU6050_ADDR_68);
  Wire.write(PWR_MGMT_1);
  Wire.write(0x00);  // Clear sleep mode
  Wire.endTransmission();
}

void check_initial_gravity(bool _initial_gravity_ok) {
  while (!initial_gravity_ok) {
    initial_gravity = get_initial_acceleration();
    if (initial_gravity != "error") {
      initial_gravity_ok = true;
    }
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
    String dataToSend = "*, " + String(_gx68) + ", " + String(_gy68) + ", " + String(_gz68) + "\n ";
    delay(500);
    return dataToSend;
  }

  else {
    return "error";
  }
}

String get_quaternion_and_acceleration() {
  // FIFO storage buffers
  uint8_t fifo_buffer68[64];  // FIFO storage buffer

  // Orientation/motion vars for successive motion elaboration
  Quaternion q68;         // [w, x, y, z]
  Quaternion last_q68;    // [w, x, y, z]
  Quaternion q69;         // [w, x, y, z]
  Quaternion last_q69;    // [w, x, y, z]
  VectorInt16 a68;        // [x, y, z]
  VectorInt16 a69;        // [x, y, z]
  VectorInt16 aReal68;    // [x, y, z]
  VectorInt16 aReal69;    // [x, y, z]
  VectorFloat gravity68;  // [x, y, z]
  VectorFloat gravity69;  // [x, y, z]

  // test the connection before trying to get the data
  while (!mpu68.testConnection()) {
    reset_I2C();
  }

  // Get the Latest packet
  if (!mpu68.dmpGetCurrentFIFOPacket(fifo_buffer68)) {
    return "data corrupted in buffer\n";
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
  String dataToSend = "#, " + String(currentTime) + ", " + String(q68.w, 2) + ", " + String(q68.x, 2) + ", " + String(q68.y, 2) + ", " + String(q68.z, 2) + ", " + String(ax) + ", " + String(ay) + ", " + String(az) + "\n ";

  delay(50);
  return dataToSend;
}

String get_next_file_name() {
    int fileIndex = 1;  // Start from 1
    String filename;
    
    do {
        filename = "/recording_" + String(fileIndex) + ".txt";
        fileIndex++;
    } while (SPIFFS.exists(filename));  // Keep increasing until an unused name is found
    
    return filename;
}

void write_file(String path, const String &message) {
  File file = SPIFFS.open(path, FILE_APPEND);
  delay(30);
  if (!file) {
    return;
  }
  file.print(message);
  file.close();
}

void list_files() {
    File root = SPIFFS.open("/");
    File file = root.openNextFile();

    Serial.println("📂 Saved Files:");
    pCharacteristic->setValue("📂 Saved Files:\n");
    pCharacteristic->notify();

    while (file) {
        Serial.println(file.name());  // Print file name
        pCharacteristic->setValue(file.name());
        pCharacteristic->notify();
        pCharacteristic->setValue("\n");
        pCharacteristic->notify();
        file = root.openNextFile();
    }
}

void send_saved_data(String _file_name) {
  File file = SPIFFS.open(_file_name, FILE_READ);

  while (file.available()) {
    String line = file.readStringUntil('\n');
    Serial.println("Sending: " + line);

    pCharacteristic->setValue(line.c_str());
    pCharacteristic->notify();
    delay(100);  // Small delay to prevent overload
  }

  file.close();
  Serial.println("All saved data sent.");
}

void clear_memory() {
  SPIFFS.format();
  Serial.println("All files succesfully deleted");
  pCharacteristic->setValue("All files succesfully deleted\n");
  pCharacteristic->notify();
}

void handle_command() {
  Serial.println("Waiting for available command ...");
  pCharacteristic->setValue("Waiting for available command ...\n");
  pCharacteristic->notify();
  while (cmd != "recorded" && cmd != "live" && cmd != "clear") {
    delay(200);
  }
  
  if (cmd == "r") {
    list_files();
    String file_path = "/" + cmd;

    while (!SPIFFS.exists(file_path) && cmd != "stop") {
      Serial.println("Choose the file you want to open");
      pCharacteristic->setValue("Could not open file, choose another one\n");
      pCharacteristic->notify();
      delay(2000);
      file_path = "/" + cmd;
    }

    if (cmd != "stop") {
      send_saved_data(file_path);
    }
    cmd = "None";
  }
    
  else if (cmd == "l") {
    if (counter == 0) {
      pCharacteristic->setValue(initial_gravity.c_str());
      pCharacteristic->notify();  // ✅ Send notification
      Serial.println("📤 Sent: " + initial_gravity);
    }

    pCharacteristic->setValue(message.c_str());
    pCharacteristic->notify();  // ✅ Send notification
    Serial.println("📤 Sent: " + message);
    counter++;
  }

  else if (cmd == "c") {
    clear_memory();   
    cmd = "None";
  }
}


  
  

