import socket
import time

# Connect to ESP32
esp_ip = "192.168.4.1"  # ESP32 IP Address
esp_port = 80

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((esp_ip, esp_port))

try:
    while True:
        data = client.recv(1024)  # Receive data from ESP32
        if data:
            print(f"Received: {data.decode('utf-8')}")
        time.sleep(0.008)  # Match ESP32 data rate
except KeyboardInterrupt:
    print("Exiting...")
finally:
    client.close()
