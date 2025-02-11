
def parse_data_one_sensor(data):
    try:
        data_list = data.strip().split(',')
        data_type = data_list[0]
        if data_type == "*":
            gx, gy, gz =  map(float, data_list[1:])
            return data_list[0], [gx, gy, gz]
        elif data_type == "#":
            timestamp, q_w, q_x, q_y, q_z, a_x, a_y, a_z = map(float, data_list[1:])
            three_quaternion = (q_x, q_y, q_z, q_w)
            accelerations = (a_x, a_y, a_z)
            return data_type, [timestamp, three_quaternion, accelerations]
    except ValueError:
        print(f"Invalid data format: {data}")

    return None, None

def parse_data_two_sensors(data):
    try:
        data_list = data.strip().split(',')
        data_type = data_list[0]
        if data_type == "*":
            gx1, gy1, gz1, gx2, gy2, gz2 = map(float, data_list[1:])
            return data_type, [gx1, gy1, gz1], [gx2, gy2, gz2]
        elif data_type == "#":
            timestamp, q1_w, q1_x, q1_y, q1_z, a1_x, a1_y, a1_z, q2_w, q2_x, q2_y, q2_z, a2_x, a2_y, a2_z = map(float, data_list[1:])
            three_quaternion_sensor_1 = (q1_x, q1_y, q1_z, q1_w)
            acceleration_sensor_1 = (a1_x, a1_y, a1_z)
            three_quaternion_sensor_2 = (q2_x, q2_y, q2_z, q2_w)
            acceleration_sensor_2 = (a2_x, a2_y, a2_z)
            return data_type, [timestamp, three_quaternion_sensor_1, acceleration_sensor_1], [timestamp, three_quaternion_sensor_2, acceleration_sensor_2]
        return data_type, None, None
    except ValueError:
        print(f"Invalid data format: {data}")

    return None, None, None

