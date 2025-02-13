#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps612.h"

#define MPU6050_ADDR_68 0x68  // I2C address of MPU6050
#define MPU6050_ADDR_69 0x69  // I2C address of MPU6050
#define ACCEL_XOUT_H 0x3B  // First register of accelerometer data
#define PWR_MGMT_1   0x6B  // Power management register

// Constants to convert acceleration
float ACCEL_SCALE = 16384.0;
float GRAVITY = 9.81;

// MPUs with their I2C ID
MPU6050 mpu68(MPU6050_ADDR_68);
MPU6050 mpu69(MPU6050_ADDR_69);

// FIFO storage buffers
uint8_t fifo_buffer68[64];  // FIFO storage buffer
uint8_t fifo_buffer69[64];  // FIFO storage buffer

// Error state variable (0 = success, !0 = error)
uint8_t error_code = 0U;  

// Orientation/motion vars for initial calibration
// raw accelerations
int16_t _ax68, _ay68, _az68;
int16_t _ax69, _ay69, _az69;

// raw accelerations in m/s^2
int16_t _gx68, _gy68, _gz68;
int16_t _gx69, _gy69, _gz69;

// Orientation/motion vars for successive motion elaboration
Quaternion q68;  // [w, x, y, z]         
Quaternion q69;  // [w, x, y, z]         
VectorInt16 a68; // [x, y, z]            
VectorInt16 a69; // [x, y, z]            
VectorInt16 aReal68; // [x, y, z] 
VectorInt16 aReal69; // [x, y, z] 
VectorFloat gravity68; // [x, y, z] 
VectorFloat gravity69; // [x, y, z] 

// Other variables
int device_number;
int loop_number;

// PROTOTYPES
void resetI2C();
int device_count();
void set_MPU6050(int _device_number);
void device_calibration(int _device_number);
void get_initial_acceleration(int _device_number);
void get_quaternion_and_acceleration(int _device_number);

// MAIN
void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(100000);
  delay(5000);

  device_number = device_count();
  set_MPU6050(device_number);

  // send 10 values of gravity on the 3 axis [elaborated to understand the initial rotation]
  while (loop_number <10) {
    get_initial_acceleration(device_number);
    loop_number++;
  } 
  
  device_calibration(device_number);
}

void loop() {
  get_quaternion_and_acceleration(device_number);
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

void set_MPU6050(int _device_number) {
  if (_device_number == 1) {
    // Wake up MPU6050 (it starts in sleep mode)
    Wire.beginTransmission(MPU6050_ADDR_68);
    Wire.write(PWR_MGMT_1);
    Wire.write(0x00);  // Clear sleep mode
    Wire.endTransmission();
  }
  else {
    Wire.beginTransmission(MPU6050_ADDR_68);
    Wire.write(PWR_MGMT_1);
    Wire.write(0x00);  // Clear sleep mode
    Wire.endTransmission();
    Wire.beginTransmission(MPU6050_ADDR_69);
    Wire.write(PWR_MGMT_1);
    Wire.write(0x00);  // Clear sleep mode
    Wire.endTransmission();
  }
}

void get_initial_acceleration(int _device_number){
  if (_device_number == 1) {
    Wire.beginTransmission(MPU6050_ADDR_68);
    Wire.write(ACCEL_XOUT_H);  // Start reading from ACCEL_XOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050_ADDR_68, 6, true);  // Request 6 bytes

    _ax68 = (Wire.read() << 8) | Wire.read();  // X-axis
    _ay68 = (Wire.read() << 8) | Wire.read();  // Y-axis
    _az68 = (Wire.read() << 8) | Wire.read();  // Z-axis

    float _gx68 = _ax68 / ACCEL_SCALE * GRAVITY;
    float _gy68 = _ay68 / ACCEL_SCALE * GRAVITY;
    float _gz68 = _az68 / ACCEL_SCALE * GRAVITY;

    if (_gx68 != 0 && _gy68 != 0 && _gz68 != 0) {
      String dataToSend = "*-, " + 
                        String(_gx68) + ", " +
                        String(_gy68) + ", " +
                        String(_gz68) + "\n ";

      Serial.print(dataToSend);
    }

    delay(500);
  }

  else {
    Wire.beginTransmission(MPU6050_ADDR_68);
    Wire.write(ACCEL_XOUT_H);  // Start reading from ACCEL_XOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050_ADDR_68, 6, true);  // Request 6 bytes

    _ax68 = (Wire.read() << 8) | Wire.read();  // X-axis
    _ay68 = (Wire.read() << 8) | Wire.read();  // Y-axis
    _az68 = (Wire.read() << 8) | Wire.read();  // Z-axis

    Wire.beginTransmission(MPU6050_ADDR_69);
    Wire.write(ACCEL_XOUT_H);  // Start reading from ACCEL_XOUT_H
    Wire.endTransmission(false);
    Wire.requestFrom(MPU6050_ADDR_69, 6, true);  // Request 6 bytes

    _ax69 = (Wire.read() << 8) | Wire.read();  // X-axis
    _ay69 = (Wire.read() << 8) | Wire.read();  // Y-axis
    _az69 = (Wire.read() << 8) | Wire.read();  // Z-axis
    
    float _gx68 = _ax68 / ACCEL_SCALE * GRAVITY;
    float _gy68 = _ay68 / ACCEL_SCALE * GRAVITY;
    float _gz68 = _az68 / ACCEL_SCALE * GRAVITY;
    float _gx69 = _ax69 / ACCEL_SCALE * GRAVITY;
    float _gy69 = _ay69 / ACCEL_SCALE * GRAVITY;
    float _gz69 = _az69 / ACCEL_SCALE * GRAVITY;
  
    if (_gx68 != 0 && _gy68 != 0 && _gz68 != 0 && _gx69 != 0 && _gy69 != 0 && _gz69 != 0) {
      String dataToSend = "**, " + 
                        String(_gx68) + ", " +
                        String(_gy68) + ", " +
                        String(_gz68) + ", " +
                        String(_gx69) + ", " +
                        String(_gy69) + ", " +
                        String(_gz69) + "\n ";
                        
      Serial.print(dataToSend);
    }

    delay(500);
  }    
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
  }

  else {
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

void get_quaternion_and_acceleration(int _device_number) {
  if (_device_number == 1) {
    // test the connection before trying to get the data
    while (!mpu68.testConnection()) {
      resetI2C();
    }

    // Get the Latest packet 
    if (!mpu68.dmpGetCurrentFIFOPacket(fifo_buffer68)) {
      return;
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
    String dataToSend = "#-, " + 
                        String(currentTime) + ", " + 
                        String(q68.w, 2) + ", " + 
                        String(q68.x, 2) + ", " + 
                        String(q68.y, 2) + ", " + 
                        String(q68.z, 2) + ", " +
                        String(ax) + ", " +
                        String(ay) + ", " +
                        String(az) + "\n ";

    Serial.print(dataToSend);
    delay(50);
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
    mpu68.dmpGetAccel(&a68, fifo_buffer68);
    mpu68.dmpGetGravity(&gravity68, &q68);
    mpu68.dmpGetLinearAccel(&aReal68, &a68, &gravity68);
    mpu69.dmpGetQuaternion(&q69, fifo_buffer69);
    mpu69.dmpGetAccel(&a69, fifo_buffer69);
    mpu69.dmpGetGravity(&gravity69, &q69);
    mpu69.dmpGetLinearAccel(&aReal69, &a69, &gravity69);

    // Get the timestamp
    unsigned long currentTime = millis();

    // Convert acceleration into multiples of g
    float ax_68 = aReal68.x / ACCEL_SCALE * GRAVITY;
    float ay_68 = aReal68.y / ACCEL_SCALE * GRAVITY;
    float az_68 = aReal68.z / ACCEL_SCALE * GRAVITY;
    float ax_69 = aReal69.x / ACCEL_SCALE * GRAVITY;
    float ay_69 = aReal69.y / ACCEL_SCALE * GRAVITY;
    float az_69 = aReal69.z / ACCEL_SCALE * GRAVITY;



    // Print the timestamp and quaternions
    String dataToSend = "##, " + 
                        String(currentTime) + ", " + 
                        String(q68.w, 2) + ", " + 
                        String(q68.x, 2) + ", " + 
                        String(q68.y, 2) + ", " + 
                        String(q68.z, 2) + ", " + 
                        String(ax_68) + ", " +
                        String(ay_68) + ", " +
                        String(az_68) + ", " +
                        String(q69.w, 2) + ", " + 
                        String(q69.x, 2) + ", " + 
                        String(q69.y, 2) + ", " + 
                        String(q69.z, 2) + ", " +
                        String(ax_69) + ", " +
                        String(ay_69) + ", " +
                        String(az_69) + "\n ";

    Serial.print(dataToSend);
    delay(50);
  }
}


