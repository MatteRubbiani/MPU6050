import matplotlib.pyplot as plt
import time
import serial
from quat_accel_pos import compute_position, rotate_acceleration


def parse_data(data):
    # Assumes data is in the format: "w, x , y , z, ax, ay, az \n" (comma-separated)
    try:
        w, x, y, z, ax, ay, az = map(float, data.strip().split(','))
        return (w, x, y, z), (ax, ay, az)
    except ValueError:
        print(f"Invalid data format: {data}")
        return None


def q_conjugate(_q):
    w, x, y, z = _q
    return w, -x, -y, -z


def q_mult(q1, q2):
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
    z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
    return w, x, y, z


def qv_mult(q1, _v1):
    q2 = (0.0,) + _v1
    return q_mult(q_mult(q1, q2), q_conjugate(q1))[1:]


def update_plot(vector):
    ax.quiver(0, 0, 0, vector[0], vector[1], vector[2], color='b')
    fig.canvas.draw()
    fig.canvas.flush_events()

ARDUINO_PORT = "COM5"
BAUD_RATE = 115200

# Open the serial connection
try:
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    ser.reset_input_buffer()
    print(f"Connected to Arduino on {ARDUINO_PORT}")
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    exit(1)

# step 1, initialize vector and plot
V_1 = (1, 0, 0)

plt.ion()
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.quiver(0, 0, 0, V_1[0], V_1[1], V_1[2], color='b')

quaternions = [[1.0, 0.0, 0.0, 0.0]]
rotated_accelerations = [[0.0, 0.0, 0.0]]
timestamps = [0]

try:
    while True:
        time.sleep(0.1)
        if ser.in_waiting > 0:
            raw_data = ser.readline().decode('utf-8').strip()
            print(raw_data)
            quaternion, accelerations = parse_data(raw_data)
            timestamps.append(timestamps[-1] + 0.1)
            quaternions.append(quaternion)
            rotated_accelerations.append(rotate_acceleration(accelerations))
            print(compute_position(accelerations, quaternions))
            """if quaternion:
                v_new_position = qv_mult(quaternion, V_1)
                update_plot(v_new_position)"""



except KeyboardInterrupt:
    print("Exiting program.")

finally:
    # Close the serial connection
    ser.close()
    print("Serial connection closed.")
