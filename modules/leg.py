from modules.sensor import Sensor


class Leg:
    def __init__(self, sensor_1:Sensor, sensor_2:Sensor):
        self.sensor_1 = sensor_1
        self.sensor_2 = sensor_2

    def  get_leg_pose(self, data_type):
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
