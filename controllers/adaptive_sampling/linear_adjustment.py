# now add to radio
# add to rover samples taken array [rov1_num_samples, rov2_num_samples]
# total samples taken for each rover
# when one rover reaches the designated total stop
#redo based on proportional

def linear_sampling_waypoints(rov):
    """
    Linear Sampler where sampling positions adjusted depending flux
    """
    if(len(rov.measured_samples)> 3):
        rov._change_metric.append(abs(rov.measured_samples[-3]/rov.measured_samples[-2]))
        rov._change_metric.append(abs(rov.measured_samples[-2]/rov.measured_samples[-1]))
    
    if(rov._change_metric[1] > rov._change_metric[0]):
        rov._sample_dist += 50
    else:
        if(rov.sample_dist > 100):
            rov._sample_dist -= 50

def sample_difference(rov):
    """
    Proporinal Sampler where sampling positions adjusted depending flux
    """
    sample_difference = []
    if(len(rov.measured_samples)> 3):
        sample_difference.append(rov.measured_samples[-3][2] - rov.measured_samples[-2][2])
        sample_difference.append(rov.measured_samples[-2][2] - rov.measured_samples[-1][2])

        rov.update_change_metric(abs(sample_difference[1] - sample_difference[0]))        

def linear_adjusted_sampler(rov, world, s_max, s_min):
    """
    Adaptive sampler sampling at regular intervals
    Linear or proportional adjustment of distance to next waypoint
    """

    if((world._dt*world._tn == 0) or \
            (len(rov.measured_samples) > 0 and rov.pose[1]-rov.measured_samples[-1][1] >= rov.sample_dist)):
        if(rov.num_samples < rov.max_num_samples and rov.is_sampling == False):
            rov._is_sampling = True
            rov._num_samples += 1
            print("Rover {} is taking a sample.".format(str(rov._rov_id)))

    if(rov.req_sampling_steps == rov.sampling_steps_passed):
        p = rov.pose.copy()
        p[0], p[1] = round(p[0]), round(p[1])
        metric_measurement = round(world._sample_metric.sample(p[0], p[1]), 5)
        rov._sampling_steps_passed = 0
        rov._measured_samples.append([p[0], p[1], metric_measurement])
        # sample_difference(rov)
        rov.update_sample_dist()
        rov._is_sampling = False
    elif(rov.is_sampling):
        rov.sampling_steps_passed += 1