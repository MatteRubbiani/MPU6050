import numpy as np
from scipy.spatial.transform import Rotation as R

from modules.sensor import Sensor


class Leg:
    def __init__(self, sensor_1:Sensor, sensor_2:Sensor, femur_length=5, tibia_length=5, hip_position=None, foot_position=None, locked_foot=False):
        self.sensor_1 = sensor_1
        self.sensor_2 = sensor_2
        self.femur_length = femur_length
        self.tibia_length = tibia_length
        self.locked_foot = locked_foot

        self.locked_hip_position = np.array(hip_position)
        self.locked_foot_position = np.array(foot_position)
        if locked_foot and foot_position is None:
            print("LOCKED FOOT but NO FOOT POSITION specified, setting to (0, 0, 0)")
            self.locked_foot_position = (0, 0, 0)
        if not locked_foot and hip_position is None:
            print("LOCKED HIP but NO HIP POSITION specified, setting to (0, 10, 0)")
            self.locked_hip_position = (0, 10, 0)

        self.current_hip_position = None
        self.target_femur_quaternion = None
        self.target_tibia_quaternion = None
        self.tibia_quaternion_as_child = None

    # questi sono dati  puri dei sensori
    def get_sensor_pose(self):
        sensor_1_current_prop = self.sensor_1.get_current_properties()
        sensor_2_current_prop = self.sensor_2.get_current_properties()

        data_to_send_femur = None
        data_to_send_tibia = None
        if sensor_1_current_prop:
            data_to_send_femur = sensor_1_current_prop
            data_to_send_femur["data_type"] = "#" # a breve tolgo
        if sensor_2_current_prop:
            pass

        data_to_publish = {
            "sensor_1" : data_to_send_femur,
            "sensor_2" : data_to_send_tibia,
        }
        return data_to_publish

    def update_pose_v1(self):
        self.target_femur_quaternion = np.array(self.sensor_1.get_pose()["quaternion"])
        self.target_tibia_quaternion = np.array(self.sensor_2.get_pose()["quaternion"])

        # Convert to Rotation objects
        r_parent_target = R.from_quat(self.target_femur_quaternion)
        r_child_target = R.from_quat(self.target_tibia_quaternion)

        # Compute the child's local rotation:
        r_child_local = r_parent_target.inv() * r_child_target
        q_child_local = r_child_local.as_quat()
        self.tibia_quaternion_as_child = q_child_local
        if self.locked_foot:
            # Convert to Rotation objects
            r_parent_target = R.from_quat(self.target_femur_quaternion)
            r_child_target = R.from_quat(self.target_tibia_quaternion)

            initial_femur_vector = np.array([0, -self.femur_length, 0])
            initial_tibia_vector = np.array([0, -self.tibia_length, 0])

            rotated_femur_vector = r_parent_target.apply(initial_femur_vector)
            rotated_tibia_vector = r_child_target.apply(initial_tibia_vector)

            # sum_vector = foot_pos - hip_pos by definition
            sum_vector = rotated_femur_vector + rotated_tibia_vector
            hip_pos = self.locked_foot_position - sum_vector
            self.current_hip_position = hip_pos
        else:
            self.current_hip_position = self.locked_hip_position

    def get_leg_pose_v1(self):
        if (self.target_femur_quaternion is None) or (self.target_tibia_quaternion is None):
            print("quaternions must be updated at least once")
            return None

        data_to_send = {
            "hip_position" : self.current_hip_position.tolist(),
            "femur_quaternion" : self.target_femur_quaternion.tolist(),
            "tibia_quaternion" : self.tibia_quaternion_as_child.tolist(),
        }

        return data_to_send

if __name__ == "__main__":
    sensor_1 = Sensor()
    sensor_2 = Sensor()

    sensor_1.add_recording(0, [0, 0, 0, 1], [0, 0, 0])
    sensor_2.add_recording(0, [0, 0, 0, 1], [0, 0, 0])

    leg = Leg(sensor_1, sensor_2, hip_position=(0, 5, 0), locked_foot=False)
    leg.update_pose_v1()
    print(leg.get_leg_pose_v1())

