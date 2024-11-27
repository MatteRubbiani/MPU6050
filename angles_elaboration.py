import numpy as np


def angle_between_vectors(u, v):
    """
    Calculate the angle between two vectors using the cross product.

    Parameters:
    u, v : array-like
        Input vectors.

    Returns:
    tuple
        The angle between the vectors in radians and degrees.
    """
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

# Prova

u = [2, 3, 4]
v = [1, 1, 1]
angle_degrees = angle_between_vectors(u, v)
print(angle_degrees)