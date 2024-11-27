import numpy as np

def calculate_angle_between_vectors(u, v):

    # Calculate the angle between two vectors using the cross product.

    # Parameters:
    # u, v : array-like, Input vectors.

    # Returns:
    # The angle between the vectors in degrees.

    u = np.array(u)
    v = np.array(v)

    cross_product = np.cross(u, v)
    magnitude_u = np.linalg.norm(u)
    magnitude_v = np.linalg.norm(v)
    magnitude_cross = np.linalg.norm(cross_product)

    sin_theta = magnitude_cross / (magnitude_u * magnitude_v)
    sin_theta = np.clip(sin_theta, -1.0, 1.0)  # Ensure sin_theta is within the valid range

    angle_radians = np.arcsin(sin_theta)
    angle_degrees = np.degrees(angle_radians)

    return angle_degrees

def calculate_angular_velocity(final_angle, initial_angle, final_timestamp, initial_timestamp):

    # Calculate the angular velocity of flexion and extension

    # Parameters:
    # final_angle, initial_angle in degrees
    # final_timestamp, initial_timestamp in ms

    # Returns:
    # Angular velocity in deg/s

    delta_angle = final_angle - initial_angle
    delta_timestamp = (final_timestamp - initial_timestamp) / 1000

    return delta_angle / delta_timestamp

# Prova
u = [2, 3, 4]
v = [1, 1, 1]
initial_angle_degrees = calculate_angle_between_vectors(u, v)
final_angle_degrees = 25
print(initial_angle_degrees)
print(calculate_angular_velocity(final_angle_degrees, initial_angle_degrees, 2, 0))