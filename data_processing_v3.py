def parse_data_v3(raw_data):
    split_data = raw_data.split(',')
    data_type = split_data[0]
    split_data = split_data[1:]
    split_data = [float(i) for i in split_data]
    # ONE SENSOR

    # *-, gx, gy, gz  [x, y, z from the point of view of sensor]
    if data_type == '*-' or data_type == '-*':
        gx, gy, gz = split_data
        return data_type, [gx, gy, gz]

    # #-, timestamp, q_w, q_x, q_y, q_z, a_x, a_y, a_z  [a is without gravity]
    if data_type == '#-' or data_type == '-#':
        timestamp, q_w, q_x, q_y, q_z, a_x, a_y, a_z = split_data
        return data_type, [timestamp, [q_x, q_y, q_z, q_w], [a_x, a_y, a_z]]

    # TWO SENSORS

    # **, gx(68), gy(68), gz(68), gx(69), gy(69), gz(69)
    if data_type == '**':
        gx_68, gy_68, gz_68, gx_69, gy_69, gz_69 = split_data
        return data_type, [gx_68, gy_68, gz_68], [gx_69, gy_69, gz_69]

    # ##, timestamp, q_w(68), q_x(68), q_y(68), q_z(68), a_x(68), a_y(68), a_z(68), q_w(69), q_x(69), q_y(69), q_z(69), a_x(69), a_y(69), a_z(69)  [a is without gravity]
    if data_type == '##':
        timestamp, q_w_68, q_x_68, q_y_68, q_z_68, a_x_68, a_y_68, a_z_68, q_w_69, q_x_69, q_y_69, q_z_69, a_x_69, a_y_69, a_z_69  = split_data
        return data_type, [timestamp, [q_x_68, q_y_68, q_z_68, q_w_68], [a_x_68, a_y_68, a_z_68]], [timestamp, [q_x_69, q_y_69, q_z_69, q_w_69], [a_x_69, a_y_69, a_z_69]]

    return data_type

print(parse_data_v3("#-,1233,1,0,0,0,9,8,9"))