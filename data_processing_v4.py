def parse_data_v4(raw_data):
    split_data = raw_data.split(',')
    data_type = split_data[0]
    split_data = split_data[1:]
    split_data = [float(i) for i in split_data]

    data_to_return = {
        "data_type": data_type
    }
    # ONE SENSOR

    # *, gx, gy, gz  [x, y, z from the point of view of sensor]
    if data_type == '*':
        gx, gy, gz = split_data
        data_to_return['g'] = [gx, gy, gz]

    # #, timestamp, q_w, q_x, q_y, q_z, a_x, a_y, a_z  [a is without gravity]
    if data_type == '#':
        timestamp, q_w, q_x, q_y, q_z, a_x, a_y, a_z = split_data
        data_to_return['timestamp'] = timestamp
        data_to_return['quaternion'] = [q_x, q_y, q_z, q_w]
        data_to_return['acceleration'] = [a_x, a_y, a_z]

    return data_to_return
