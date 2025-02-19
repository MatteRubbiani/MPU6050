#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>  // Required for notifications

// UUIDs for Service & Characteristic (Must match Python script)
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

// Callback for device connection
class MyServerCallbacks : public BLEServerCallbacks {
    void onConnect(BLEServer* pServer) {
        deviceConnected = true;
        Serial.println("✅ Device connected!");
    }

    void onDisconnect(BLEServer* pServer) {
        deviceConnected = false;
        Serial.println("🔴 Device disconnected...");
        BLEDevice::startAdvertising();  // Restart advertising
    }
};

void setup() {
    Serial.begin(115200);
    Serial.println("🔵 Starting BLE...");

    // Initialize BLE
    BLEDevice::init("Long name works now");
    BLEServer *pServer = BLEDevice::createServer();
    pServer->setCallbacks(new MyServerCallbacks());

    // Create Service
    BLEService *pService = pServer->createService(SERVICE_UUID);

    // Create Characteristic with NOTIFY property
    pCharacteristic = pService->createCharacteristic(
        CHARACTERISTIC_UUID,
        BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
    );

    // Required for notifications to work
    pCharacteristic->addDescriptor(new BLE2902());

    // Start Service
    pService->start();

    // Start Advertising
    BLEAdvertising *pAdvertising = BLEDevice::getAdvertising();
    pAdvertising->addServiceUUID(SERVICE_UUID);
    pAdvertising->start();

    Serial.println("📡 BLE Advertising...");
}

void loop() {
    static int counter = 0;

    if (deviceConnected) {
        String message = "##," + String(counter++) + ",1,0,0,0,0,0,0,1,0,0,0,0,0,0";
        pCharacteristic->setValue(message.c_str());
        pCharacteristic->notify();  // ✅ Send notification

        Serial.println("📤 Sent: " + message);
    }

    delay(50);
}
