import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import time
import os
import datetime as dt
import statistics as stats
import random as rand

from models.world import *
from models.slope_physics import *
from models.P_controller import *
from models.pose_logger import *
from utils.load_map import *
from utils.render import *
from utils.path import *
from utils.graphs import *
from sampling_metric import *


BW = [125, 250, 500]                # Selectable bandwidth, in KHz.
SF = [6, 7, 8, 9, 10, 11, 12]       # Selectable spreading factor.
CR = [4 / 5, 4 / 6, 4 / 7, 4 / 8]   # Selectable coding rate.

# Configure basic simulation settings:
area = 'TL16NW'     # Area to run simulation.
N = 10              # Number of rovers.
rovers_sep = 450          # Distance between rovers, in meter.
x_offset = 475      # Offset from left boundary in easting direction, in meter.
y_offset = 5        # Offset from baseline in northing direction, in meter.
goal_offset = 5     # Of distance to goal is smaller than offset, goal is assumed reached, in meter.
max_time = 43200    #43200      # Maximum time for mission in seconds

t_sampling = 0.12     # Sampling time, in second. 0.12 FOR LS

Q = None                                        # State noise.
R = None                                        # Measurement noise.
seed_value = dt.datetime.now().microsecond      # Seed value for noise 
rand.seed(seed_value)

# Log control First bit is raw data, 2nd bit = Summary Data 3rd bit = Graph
log_control = '111'
log_step_interval = 60                                  #60 seconds which is 1 minute
log_title_tag = "Path Planned AS MVG"
log_title = log_title_tag + ', ' + str(dt.datetime.now())[:-7].replace(':', '-')
log_notes = '''Tx_pw set to rightful 14'''             #Additional notes to be added to Log file if wished
log_cp_interval = 1800                                 #Log every 30 minutes = 1800 seconds

# Configure communication settings:
user_f = 869.525                                    # Carrier center frequency, in MHz.
user_bw = BW[0]                                     # Bandwidth, in kHz.
user_sf = SF[3]                                     # Spreading factor.
user_cr = CR[3]                                     # Coding rate.
user_txpw = 14                                      # Transmitting power, in dBm.
user_dc = 1                                         # Duty cycle in %

# Configure control settings:
ctrl_policy = '3-2'
# Control policy:
# 0 - meaning no controller.
# 1 - meaning goal-driven controller, if used:
K_goal = [1e-1, 1e-1]                                       # Control gain for goal-driven controller;

# 2/3 - meaning passive-cooperative controller, if used:
K_neighbour = [0, 1e-1]                                     # Control gain for passive-cooperative controller;
decay = 'quad'
zero_crossing = 20                                          # Num of communication cycles for it to fully decay

# Advance Line Sweeping Parameter
num_of_waypoints = 10                                       # Number of waypoints
load_waypoints = True                                       # Do you want to load wapoints from another simulation
waypoints_file = os.getcwd() + '\\' + 'logs\\TL16NW\\control_policy_2-1\\FINAL Run, 2022-04-27 18-51-19\\SSS Parameters.txt'            # Directory and name of file


# 4 Adaptive Sampling Parameters
metric_mean = ['R', 'T']                                    #[0]: (L)eft, (M)iddle, (R)ight, [1]: (T)op, (M)iddle, (B)ottom
metric_covariance = [[2, 1], [0, 1]]
K_sampler = [0.1, 3.25, 0.75]                             # dist * K[1]/ (K[0] + 1)Gains for sampler [0]: is own sampling change [2]: neighbouring samples [1]: natural increase gain # 500 4, [0.1, 3.25, 0.75][200, 3.25, 0.25] 
num_r_samples = 20                                          # Determines default sampling distance
sampling_time = 600                                         # How long it takes to correctly take a sample in seconds
metric_order = 0                                            # What metric we are measuring


def main():
    """
    The very first simulation.
    """
    print('')
    print('Simulating...')

    start = time.time()

    CP = ctrl_policy.split('-')
    CP[0] = int(CP[0])
    CP[1] = int(CP[1])

    if(CP[0] == 1):
        mission = 'LS'
    elif(CP[0] == 2):
        mission = 'ALS'
    elif(CP[0] == 3):
    
        mission = 'AS'
    
    log_cp_inter = math.ceil(log_cp_interval / t_sampling)
    log_step_inter = math.ceil(log_step_interval / t_sampling)
    s_time = math.ceil(sampling_time / t_sampling)
    max_steps = math.ceil(max_time / t_sampling)

    # Load terrain map and land cover map to create the world.
    # Configure world's dynamics engine.
    map_terrain = read_asc(locate_map(area + '_elevation' + '.asc'))
    map_landcover = read_asc(locate_map(area + '_landcover' + '.asc'))
    x_min, x_max = map_terrain.x_llcorner, map_terrain.x_llcorner + map_terrain.x_range
    y_min, y_max = map_terrain.y_llcorner, map_terrain.y_llcorner + map_terrain.y_range


    world = World(map_terrain, map_landcover, mission, t_sampling)
    world.config_sample_metric(Sampling_Metric(x_min, x_max, y_min, y_max), metric_mean, metric_covariance)
    world.config_engine(SlopePhysics(world))

    init_waypoints = []
    if(load_waypoints):
        get_waypoints(waypoints_file, init_waypoints)

    image, axis_range = render_rgb(map_landcover)
    fig0 = show_rgb_waypoints(image, axis_range, init_waypoints, load_waypoints, x_offset, y_offset, \
        goal_offset, rovers_sep, N, num_of_waypoints)

    for i in range(len(init_waypoints)):
        for j in range(len(init_waypoints[i])):
            init_waypoints[i][j] = init_waypoints[i][j][:2]

    s_dist = round((y_max-y_min) / (num_r_samples-1), 3)
    # Add rovers to the world.
    for i in range(N):
        world.add_rover(init_waypoints[i][0][0], init_waypoints[i][0][1], init_waypoints[i], q_noise=Q, r_noise=R, num_rovers=N)

    # Configure rovers' settings.
    for starter in world.rovers:
        starter.config_radio(user_f, user_bw, user_sf, user_cr, user_dc, user_txpw)
        starter.radio.set_swarm_size(N)
        starter.radio.config_de()
        starter.radio.config_silent_time()
        starter.radio.set_t_slot(t_sampling)

        # Configure motion logger.
        starter.config_pose_logger(PoseLogger(starter))

        # Set goal point for each rover.
        starter.set_current_goal(starter.waypoints[1])

        # Configure controller.
        if CP[0] == 1 or CP[0] == 2:
            if CP[1] == 0:  # No controller
                pass
            elif CP[1] == 1:  # Goal-driven controller
                speed_controller = PController(None, K_goal)
                # The reference is goal point [x_g, y_g],
                # which is set differently for each rover.
                starter.config_speed_controller(speed_controller)
                starter.speed_controller.set_ref(starter.goal)
                full_mission_name = 'Goal-driven'
                starter.config_control_policy(full_mission_name)
            elif CP[1] == 2:  # Passive-cooperative controller
                speed_controller = PController(None, K_neighbour)
                starter.config_speed_controller(speed_controller)
                # The reference for passive-cooperative controller
                # dynamically changes when new packet from the neighbour is received.
                full_mission_name = 'Simple Passive-cooperative'
                starter.config_control_policy(full_mission_name)
            elif CP[1] == 3:
                speed_controller = PController(None, K_neighbour)
                starter.config_speed_controller(speed_controller)
                starter.config_decay_type(decay)
                starter.config_decay_zero_crossing(zero_crossing * starter.radio.interval)
                # The reference for passive-cooperative controller
                # dynamically changes when new packet from the neighbour is received.
                full_mission_name = 'Passive-cooperative'
                starter.config_control_policy(full_mission_name)
            else:
                print("No valid controller found")
                full_mission_name = 'NA'
        elif CP[0] == 3:
            if CP[1] == 1:
                speed_controller = PController(None, K_goal)
                # The reference is goal point [x_g, y_g],
                # which is set differently for each rover.
                starter.config_speed_controller(speed_controller)
                starter.speed_controller.set_ref(starter.goal)
                full_mission_name = 'Independent Adaptive Sampling'
                starter.config_control_policy(full_mission_name)
                starter.config_adaptive_sampler_gains(K_sampler)
                starter.config_sample_dist(s_dist)
                starter.config_req_sample_steps(s_time)
                starter.config_sample_order_metric(metric_order)
            elif CP[1] == 2:
                speed_controller = PController(None, K_goal)
                # The reference is goal point [x_g, y_g],
                # which is set differently for each rover.
                starter.config_speed_controller(speed_controller)
                starter.speed_controller.set_ref(starter.goal)
                full_mission_name = 'Co-op Adaptive Sampling'
                starter.config_control_policy(full_mission_name)
                starter.config_adaptive_sampler_gains(K_sampler)
                starter.config_sample_dist(s_dist)
                starter.config_req_sample_steps(s_time)
                starter.config_sample_order_metric(metric_order)
            else:
                print("No valid controller found")
                full_mission_name = 'NA'
        else:
            print("No valid controller found.")

    # Step simulation and record data.
    ee = []  # To record formation error.
    step = 0
    while True:
        world.step()
        for l in range(N):
            world.rovers[l].pose_logger.log_pose()
            world.rovers[l].pose_logger.log_velocity()
            world.rovers[l].pose_logger.log_connectivity()

        error = 0.0
        for m in range(N - 1):  # Root mean square formation error
            error += (world.rovers[m + 1].pose_logger.y_pose[-1]
                    - world.rovers[m].pose_logger.y_pose[-1]) ** 2
        ee.append(sqrt(error / (N - 1)))
            
        step += 1

        invalid_rov_pos = False
        for n in range(N):
            if(world.rovers[n].landcover_termination):
                invalid_rov_pos = True
                break
        
        termination_reason = -1
        if world.completed_rovers == N:
            termination_reason = 0
            break
        elif invalid_rov_pos:
            termination_reason = 1
            break
        elif max_steps is not None:
            if step == max_steps:
                termination_reason = 2
                break

    total_samples = 0
    if(mission == 'AS'):
        for m in range(N):
            total_samples += world.rovers[m].num_samples


    # Simulation running time.
    end = time.time()

    # Print logged information.
    print('')
    print('=' * 50)
    print('Time elapse: {} (s)'.format(str(round(world.time, 1))))
    print('=' * 50)
    print('Motion information: ')
    print('\nMax RMSE: {} (m) @ {}s'.format(str(round(max(ee), 2)), str(round(ee.index(max(ee))*t_sampling, 2))))
    print('Mean RMSE: {} (m)'.format(str(round(stats.mean(ee), 2))))
    print('Total No. Samples: {}'.format(str(total_samples)))
    for k in range(N):
        logger = world.rovers[k].pose_logger
        print('-' * 50)
        print('Rover ID: {}'.format(str(k + 1)))
        print('Distance marched in northing: {} (m)'.format(str(round(logger.y_pose[-1] - logger.y_pose[0]))))
        print('Average speed in northing: {} (m/s)'.format(str(round(sum(logger.velocity) / len(logger.velocity), 2))))
        if logger.termination_time is None:
            print('Task not completed.')
        else:
            print('Time to Complete the Task: {} (s)'.format(str(round(logger.termination_time, 1))))
    print('=' * 50)
    print('Communication performance: ')
    for j in range(N):
        transceiver = world.rovers[j].radio
        print('-' * 50)
        print('Rover ID: {}'.format(str(j + 1)))
        print('Swarm Size: {}'.format(str(transceiver.total_radios)))
        if transceiver is None:
            print('No radio settings.')
        else:
            print('Bandwidth: {} (KHz)'.format(str(transceiver.bw)))
            print('Spreading Factor: {}'.format(str(transceiver.sf)))
            print('Coding Rate: {}/{}'.format(str(4), str(int(4 / transceiver.cr))))
            print('Sensitivity: {} (dBm)'.format(str(transceiver.sensitivity)))
            print('Transmission Power: {} (dBm)'.format(str(transceiver.tx_pw)))
            print('Antenna Gain: {} (dBi)'.format(str(transceiver.ant_gain)))
            print('Payload Length: {} (byte)'.format(str(transceiver.pl)))
            print('Duty Cycle: {}%'.format(str(round(transceiver.actual_dc() * 100, 1))))
            print('Airtime: {} (sec)'.format(str(round(transceiver.airtime(), 4))))
            print('Silent time: {} (sec)'.format(str(round(transceiver.interval * t_sampling, 1))))
            print('Transmitted Packets: {}'.format(str(transceiver.num_tx)))
            print('Received Packets: {}'.format(str(transceiver.num_rx)))
            print('Discarded Packets: {}'.format(str(transceiver.num_disc)))
            try:
                print('Packet Loss Ratio: {}%'.format(str(round(transceiver.num_disc
                                                                / (transceiver.num_rx + transceiver.num_disc) * 100, 2))))
            except ZeroDivisionError:
                print('Packet Loss Ratio: N/A')

            if(transceiver.airtime() > t_sampling):
                    print('\nWARNING: Airtime ({}) > Sample time ({}), reduces accuracy of simulation.'.format(str(transceiver.airtime()), str(t_sampling)))
    print('=' * 50)

    # Print simulation running time.
    print('')
    if termination_reason == -1:
        termination_note = "Unknown"
    elif termination_reason == 0:
        termination_note = "Mission Completed"
    elif termination_reason == 1:
        termination_note = "Rover Entered Impassable Land Cover"
    elif termination_reason == 2:
        termination_note = "Set Time Limit Reached"

    print("Termination reason:", termination_note)
    print('Simulation running time: {} (s)'.format(str(round(end - start, 1))))

    #Logs directory creation if not created
    if(int(log_control) >= 1):
        if(not os.path.exists('logs\\' + area)):
            os.mkdir(os.getcwd() + '\\logs\\' + area)
        if(not os.path.exists('logs\\' + area + '\\control_policy_' + str(ctrl_policy))):
            os.mkdir(os.getcwd() + '\\logs\\' + area+ '\\control_policy_' + str(ctrl_policy))
        if(not os.path.exists('logs\\' + area + '\\control_policy_' + str(ctrl_policy) + '\\' + str(log_title))):
            os.mkdir(os.getcwd() + '\\logs\\' + str(area) + '\\control_policy_' + str(ctrl_policy) + '\\' + str(log_title))
    directory = 'logs\\' + str(area) + '\\control_policy_' + str(ctrl_policy) + '\\' + str(log_title) + '\\'

    if(int(log_control) >= 1):
        log_parameter_file_name = 'SSS Parameters'
        log_parameter_file = open(directory + log_parameter_file_name + '.txt', 'w')
        log_parameter_file.write(log_parameter_file_name + ': ' + log_title + '\n')
        log_parameter_file.write("\nNotes: " + log_notes)
        log_parameter_file.write('\n')
        log_parameter_file.write('=' * 50)
        log_parameter_file.write("\nMission: " + full_mission_name)
        log_parameter_file.write('\n')
        log_parameter_file.write('=' * 50)
        log_parameter_file.write('\nSimulator Parameters:\n')
        log_parameter_file.write('-' * 50)
        log_parameter_file.write('''\nArea = {}\nRovers(N) = {}\nX Offset = {}\nY Offset = {}\nGoal Offset = {}\nSteps Undergone= {}
        \nMaximum Steps Allowed = {}\nSimpulation Sampling Period = {}\nNoise Seed = {}\nState Noise(Q) = {}\nMeasurement Noise(R) = {}
        \nControl Policy(ctrl_policy) = {}\nDistance between Rovers(dist) = {}'''.format(str(area), str(N), str(x_offset), str(y_offset), str(goal_offset), \
        str(step), str(max_steps), str(t_sampling), str(seed_value), str(Q), str(R), str(ctrl_policy), str(rovers_sep)))
        log_parameter_file.write('\n')
        log_parameter_file.write('=' * 50)
        log_parameter_file.write('''\nLoRa Parameters:\n''')
        log_parameter_file.write('-' * 50)
        log_parameter_file.write('''\nFrequency = {}\nBandwidth(BW) = {}\nSpreading Factor(SF) = {}\nCoding Rate(CR) = {}
        \nTransmitting Power(TxPW) = {}\nDuty Cycle = {}'''.format(str(user_f), str(user_bw), str(user_sf), str(user_cr), str(user_txpw), str(user_dc)))

        log_parameter_file.write('\n')
        log_parameter_file.write('=' * 50)
        log_parameter_file.write('\nMission Parameters:\n')
        log_parameter_file.write('-' * 50)
        if(mission[-2:] == 'LS'):
            log_parameter_file.write('''\nGoal Driven Gain = {}\nPassive Controller Gain = {}\nDecay Type = {}\nDecay Zero Crossing = {}'''.format(str(K_goal), \
                str(K_neighbour), str(decay), str(zero_crossing)))
            if(mission == 'ALS'):
                log_parameter_file.write('''\nNumber of Path Planning Waypoints = {}'''.format(str(num_of_waypoints)))
                log_parameter_file.write('''\n\nWaypoints:''')
                for x in range(N):
                    log_parameter_file.write('''\nRover {} => {}'''.format(str(x+1), str(init_waypoints[x])))
        elif(mission == 'AS'):
            log_parameter_file.write('''Metric Distirbution Mean = {}\nMetric Distribution Covariance = {}\nDefault Number of Samples = {}\nDefault Sampling Distance = {}
            \nSampler Gain = {}\nRequired Time for Sampling = {}\nNth Order Derivative Measure = {}'''.format(str(metric_mean), str(metric_covariance), str(num_r_samples), \
            str(s_dist), str(K_sampler), str(s_time), str(metric_order)))

    #Log Summary Information
    if(int(log_control[1]) == 1):
        log_summary_file_name = 'SSS Summary Data'
        log_summary_file = open(directory + log_summary_file_name+'.txt', 'w')
        log_summary_file.write(log_summary_file_name + ': ' + log_title + '\n')
        log_summary_file.write("\nNotes: " + log_notes)
        log_summary_file.write("\nMission: " + full_mission_name)
        log_summary_file.write('\n')
        log_summary_file.write('=' * 50)
        log_summary_file.write('\n')
        log_summary_file.write('=' * 50)
        log_summary_file.write('\nTime elapse: {} (s)'.format(str(round(world.time, 1))))
        log_summary_file.write('\n')
        log_summary_file.write('=' * 50)
        log_summary_file.write('\nMotion information: ')
        log_summary_file.write('\nMax RMSE: {} (m) @ {}s'.format(str(round(max(ee), 2)), str(round(ee.index(max(ee))*t_sampling, 2))))
        log_summary_file.write('\nMean RMSE: {} (m)'.format(str(round(stats.mean(ee), 2))))
        log_summary_file.write('\nTotal No. Samples: {}'.format(str(total_samples)))
        for k in range(N):
            logger = world.rovers[k].pose_logger
            log_summary_file.write('\n')
            log_summary_file.write('-' * 50)
            log_summary_file.write('\nRover ID: {}'.format(str(k + 1)))
            log_summary_file.write('\nDistance marched in northing: {} (m)'.format(str(round(logger.y_pose[-1] - logger.y_pose[0]))))
            log_summary_file.write('\nAverage speed in northing: {} (m/s)'.format(str(round(sum(logger.velocity) / len(logger.velocity), 2))))
            if logger.termination_time is None:
                log_summary_file.write('\nTask not completed.')
            else:
                log_summary_file.write('\nTime to Complete the Task: {} (s)'.format(str(round(logger.termination_time, 1))))
        log_summary_file.write('\n')
        log_summary_file.write('=' * 50)
        log_summary_file.write('\nCommunication performance: ')
        for j in range(N):
            transceiver = world.rovers[j].radio
            log_summary_file.write('\n')
            log_summary_file.write('-' * 50)
            log_summary_file.write('\nRover ID: {}'.format(str(j + 1)))
            log_summary_file.write('\nSwarm Size: {}'.format(str(transceiver.total_radios)))
            if transceiver is None:
                log_summary_file.write('\nNo radio settings.')
            else:
                log_summary_file.write('\nBandwidth: {} (KHz)'.format(str(transceiver.bw)))
                log_summary_file.write('\nSpreading Factor: {}'.format(str(transceiver.sf)))
                log_summary_file.write('\nCoding Rate: {}/{}'.format(str(4), str(int(4 / transceiver.cr))))
                log_summary_file.write('\nSensitivity: {} (dBm)'.format(str(transceiver.sensitivity)))
                log_summary_file.write('\nTransmission Power: {} (dBm)'.format(str(transceiver.tx_pw)))
                log_summary_file.write('\nAntenna Gain: {} (dBi)'.format(str(transceiver.ant_gain)))
                log_summary_file.write('\nPayload Length: {} (byte)'.format(str(transceiver.pl)))
                log_summary_file.write('\nDuty Cycle: {}%'.format(str(round(transceiver.actual_dc() * 100, 1))))
                log_summary_file.write('\nAirtime: {} (sec)'.format(str(round(transceiver.airtime(), 4))))
                log_summary_file.write('\nSilent time: {} (sec)'.format(str(round(transceiver.interval * t_sampling, 1))))
                log_summary_file.write('\nTransmitted Packets: {}'.format(str(transceiver.num_tx)))
                log_summary_file.write('\nReceived Packets: {}'.format(str(transceiver.num_rx)))
                log_summary_file.write('\nDiscarded Packets: {}'.format(str(transceiver.num_disc)))
                try:
                    log_summary_file.write('\nPacket Loss Ratio: {}%'.format(str(round(transceiver.num_disc
                                                                    / (transceiver.num_rx + transceiver.num_disc) * 100, 2))))
                except ZeroDivisionError:
                    log_summary_file.write('\nPacket Loss Ratio: N/A')
                if(transceiver.airtime() > t_sampling):
                    log_summary_file.write('\nWARNING: Airtime ({}) > Sample time ({}), reduces accuracy of simulation.'.format(str(transceiver.airtime()), str(t_sampling)))
        log_summary_file.write('\n')                                                        
        log_summary_file.write('=' * 50)

        # Log simulation running time.
        log_summary_file.write('\n')
        log_summary_file.write("Termination reason: " + termination_note)
        log_summary_file.write('\nSimulation running time: {} (s)'.format(str(round(end - start, 1))))
        log_summary_file.close()
    
    #Log Raw Data into a file
    if(int(log_control[0]) == 1):
        log_raw_file_name = 'SSS Raw Data'
        log_raw_file = open(directory + log_raw_file_name+'.txt', 'w')
        log_raw_file.write(log_raw_file_name + ': ' + log_title + '\n')
        log_raw_file.write("Notes: " + log_notes + '\n')
        log_raw_file.write('=' * 50)
        log_raw_file.write('\n')
        log_raw_file.write('=' * 50)
        log_raw_file.write("\t\t Rover\n")
        log_raw_file.write("Time\t")
        for x in range(N):
            log_raw_file.write(str(x+1) + 'x\t' + str(x+1) + 'y\t' + str(x+1) + 'v\t')
        log_raw_file.write('RMSE EE')

        for n in range(0, step+1, log_step_inter):   #+1 for velocity to calculate avg speed of the last interval.
            log_raw_file.write('\n' + str(round(n*t_sampling/60, 2)) +'\t')        #divide 60 for per minute
            data = ""
            for j in range(N):
                if(n>=log_step_inter):
                    avg_velocity = round(np.mean(world.rovers[j].pose_logger.velocity[(n-log_step_inter):n]), 3)
                else:
                    avg_velocity = round(world.rovers[j].pose_logger.velocity[n], 3)

                if(n>=step): #need last velocity interval but position index doesn't include it.
                    n = step-1

                data += str(round(world.rovers[j].pose_logger.x_pose[n], 2)) + ',' + str(round(world.rovers[j].pose_logger.y_pose[n], 2)) \
                    + ',' + str(avg_velocity) + '-'

            if(n>=log_step_inter):
                data += str(round(np.mean(ee[n-log_step_inter:n]), 3))
            else:
                data += str(round(np.mean(ee[n]), 3))
            log_raw_file.write(data)
        log_raw_file.close()
    
    #Plot and logging of graphs
    if(int(log_control[2]) == 1):
        fig0.savefig(directory + 'Path_Planned_Trajectory.png', dpi=100)


    terrain_plot(world, map_terrain, x_min, x_max, y_min, y_max, N, log_cp_inter, step, log_control[2], directory)
    RMSE_plot(world, step, log_step_inter, ee, log_control[2], directory)
    landcover_plot(world, map_landcover, x_min, x_max, y_min, y_max, N, log_cp_inter, step, log_control[2], directory)
    y_position_plot(world, step, log_step_inter, y_min, y_max, N, log_control[2], directory)
    mission_connectivity_plot(world, N, world.rovers[0].radio.interval, step, log_control[2], directory)
    # real_metric_distribution(world, directory, log_control[2])
    real_metric_distribution_overlay(world, map_terrain, directory, log_control[2])

    plt.show()
    plt.tight_layout()

if __name__ == '__main__':
    main()
