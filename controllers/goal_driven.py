from operator import imod
import math

def x_direction(value):
    if(value >= 0):
        return 1
    else:
        return -1

def ratio_speeds(rov):
    p = rov._pose
    target = rov.goal
    v = rov._control[2]
    x_diff = target[0] - p[0]
    y_diff = target[1] - p[1]
    angle = math.atan(y_diff/abs(x_diff))
    rov._angle = angle
    
    rov._control[0] = round(x_direction(x_diff) * v * math.cos(angle), 3)
    rov._control[1] = round(v * math.sin(angle), 3)


def move2goal(rov, v_max, v_min):
    """
    Move towards goal point.
    """
    offset = 5

    controlled_object = rov.measurement  # Controlled object is [x, y].
    if(rov._pose[1] > rov.goal[1]-offset):   #if within offset of the y waypoint
        rov._goal_index += 1
        rov.speed_controller.set_ref(rov.goal)
    control_input = rov._speed_controller.execute2(controlled_object)

    if control_input > v_max:  # Control input saturation.
        rov._control[2] = v_max
    elif control_input < v_min:
        rov._control[2] = v_min
    else:
        rov._control[2] = control_input  # Assume changing linear velocity instantly.

    ratio_speeds(rov)

    #return rov