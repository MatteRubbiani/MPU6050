import numpy as np

def parse_data(data):
    try:
        timestamp, w, x, y, z, w1, x1, y1, z1 = map(float, data.strip().split(', '))
        return [timestamp, [[w, x, y, z], [w1, x1, y1, z1]]]
    except ValueError:
        print(f"Invalid data format: {data}")
        return [None, None]

def quaternions_to_vectors(quaternions, tibia_start=(0, 1, 0), femur_start=(0, 1, 0)):
    quaternion_tibia = quaternions[0]
    quaternion_femur = quaternions[1]
    # tibia_new_position = qv_mult(quaternion_tibia, tibia_start)
    # femur_new_position = qv_mult(quaternion_femur, femur_start)
    tibia_new_position = rotate_vector_with_quaternion(tibia_start, quaternion_tibia)
    femur_new_position = rotate_vector_with_quaternion(femur_start, quaternion_femur)
    return tibia_new_position, femur_new_position

def q_conjugate(_q):
    w, x, y, z = _q
    return w, -x, -y, -z

# with rotation matrix
def rotate_vector_with_quaternion(vector, quaternion):
    """
    Rotates a 3D vector using a quaternion.

    Parameters:
        vector (list or np.ndarray): The 3D vector to rotate, [x, y, z].
        quaternion (list or np.ndarray): The quaternion [w, x, y, z].

    Returns:
        np.ndarray: The rotated 3D vector.
    """
    # Normalize the quaternion
    q = np.array(quaternion, dtype=float)
    q /= np.linalg.norm(q)

    # Extract quaternion components
    w, x, y, z = q

    # Compute the quaternion rotation matrix
    rotation_matrix = np.array([
        [1 - 2*y**2 - 2*z**2, 2*x*y - 2*w*z,     2*x*z + 2*w*y],
        [2*x*y + 2*w*z,     1 - 2*x**2 - 2*z**2, 2*y*z - 2*w*x],
        [2*x*z - 2*w*y,     2*y*z + 2*w*x,     1 - 2*x**2 - 2*y**2]
    ])

    # Rotate the vector
    rotated_vector = np.dot(rotation_matrix, vector)
    return list(rotated_vector)
