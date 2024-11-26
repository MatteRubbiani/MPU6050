#include "Wire.h"
#include "I2Cdev.h"
#include "MPU6050_6Axis_MotionApps612.h"

/**
 * # Wiring
 * | MPU6050 | Arduino   |
 * | ------- | --------- |
 * | GND     | GND       |
 * | VCC     | 3V3       |
 * | SCL     | SCL       |
 * | SDA     | SDA       |
 * | ADD     | see below |
 * 
 * ## ADDR pin 
 * 
 * ADDR low = 0x68 (default)
 * ADDR high = 0x69
 */

void resetI2C() {
  Wire.end();  // Termina la comunicazione I²C
  delay(100);  // Aspetta un momento
  Wire.begin();  // Riavvia il bus I²C;
}

// initialize the two MPUs with their I2C ID
MPU6050 mpu68(0x68);

uint8_t error_code = 0U;      // return status after each device operation (0 = success, !0 = error)

void setup() {
  Wire.begin();

  // it seems that we cannot use too high clock rate, due to the long I2C wire.
  // cannot flash firmware if signal integrity is too bad.
  // Wire.setClock(400000);
  Wire.setClock(10000);

  Serial.begin(115200);
  
  // initialize device
  mpu68.initialize();
  error_code = mpu68.dmpInitialize();
  
  // 1 = initial memory load failed
  // 2 = DMP configuration updates failed
  // (if it's going to break, usually the code will be 1)
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
  mpu68.CalibrateAccel(10);
  mpu68.CalibrateGyro(10);

  // calibration procedure will dump garbage on serial, we use a newline to fence it
  Serial.print("\n");
  
  // turn on the DMP, now that it's ready
  mpu68.setDMPEnabled(true);
  //mpu69.setDMPEnabled(true);
}

void loop() {
  // test the connection before trying to get the data
  while (!mpu68.testConnection()) {
    resetI2C();
  }
  
  // Get the Latest packet 
  uint8_t fifo_buffer68[64]; // FIFO storage buffer
  if (!mpu68.dmpGetCurrentFIFOPacket(fifo_buffer68)) {
    return;
  }
  Quaternion q68;
  mpu68.dmpGetQuaternion(&q68, fifo_buffer68);

  Serial.print(q68.w);Serial.print(", ");
  Serial.print(q68.x);Serial.print(", ");
  Serial.print(q68.y);Serial.print(", ");
  Serial.print(q68.z);Serial.print(", ");
  Serial.print(q68.w);Serial.print(", ");
  Serial.print(q68.x);Serial.print(", ");
  Serial.print(q68.y);Serial.print(", ");
  Serial.print(-q68.z);Serial.print("\n");

}