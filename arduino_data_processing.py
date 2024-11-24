def parse_data(data):
    # Assumes data is in the format: "w, x , y , z\n" (comma-separated)
    try:
        w, x, y, z, w1, x1, y1, z1 = map(float, data.strip().split(', '))
        return [w, x, y, z], [w1, x1, y1, z1]
    except ValueError:
        print(f"Invalid data format: {data}")
        return None

def quaternions_to_vectors(quaternions, tibia_start=(0, 0, 1), tibia_end=(0, 0, 1)):
    quaternion_tibia = quaternions[0]
    quaternion_femur = quaternions[1]
    tibia_new_position = qv_mult(quaternion_tibia, tibia_start)
    femur_new_position = qv_mult(quaternion_femur, tibia_end)
    return tibia_new_position, femur_new_position

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
