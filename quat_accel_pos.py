import numpy as np
from scipy.spatial.transform import Rotation as R


# Function to convert quaternion to a rotation matrix
def quaternion_to_rotation_matrix(quaternion):
    return R.from_quat(quaternion).as_matrix()


# Function to rotate accelerations to the global frame
def rotate_acceleration(accel, quaternion):
    rotation_matrix = quaternion_to_rotation_matrix(quaternion)
    return np.dot(rotation_matrix, accel)


# Function to compute position from accelerations
def compute_position(accelerations, timestamps):
    """
    Parameters:
        accelerations: List of 3D accelerations in sensor frame [ax, ay, az].
        quaternions: List of quaternions [qx, qy, qz, qw] for orientation.
        timestamps: List of timestamps corresponding to the measurements.
    Returns:
        positions: List of 3D positions [x, y, z].
    """
    num_samples = len(accelerations)
    positions = np.zeros((num_samples, 3))
    velocities = np.zeros((num_samples, 3))

    for i in range(1, num_samples):
        # Time difference
        dt = timestamps[i] - timestamps[i - 1]

        # Rotate acceleration to global frame -- no gia fatto
        # accel_global = rotate_acceleration(accelerations[i], quaternions[i])
        accel_global = accelerations

        # Remove gravity (assumes Z-axis aligned with gravity)
        accel_global[2] -= 9.81

        # Integrate acceleration to update velocity
        velocities[i] = velocities[i - 1] + accel_global * dt

        # Integrate velocity to update position
        positions[i] = positions[i - 1] + velocities[i] * dt

    return positions


# Example Usage:
accelerations = [[0, 0, 0], [0.1, 0.1, 9.91], [0.2, 0.1, 9.91]]  # Replace with real data
quaternions = [[0, 0, 0, 1], [0, 0, 0.1, 0.99], [0, 0, 0.2, 0.98]]  # Replace with real data
timestamps = [0, 0.1, 0.2]  # Replace with real data (in seconds)

positions = compute_position(accelerations, quaternions, timestamps)
print("Positions:\n", positions)
