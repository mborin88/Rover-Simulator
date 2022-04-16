# Rover-Simulator
## What is Rover-Simulator
Rover-Simulator is the further developement of Rover-Simulator-Zero by Yishi Fu.
Rover-Simulator is a simulator for sparse robot swarms in hilly nature environments where swarm members communicate via LoRa PHY.
Where different controllers have been developed to allow the swarm to perform different tasks. The tasks the rover can perform are:
* Line Sweep - Rovers traverse across a map keeping a line.

* Advanced Line Sweep - Further developement of line sweep where each rover follows a pre-determined path by the user.

* Adaptive Sampling - Rovers take optimal measurments of the land using an efficient method to reduce total number of samples taken.

## Downloading and Running Rover-Simulator
The standard way of downloading Rover-Simulator is by downloaidng the development sources via Git.
By running the following code on the command line:

```git clone https://github.com/mborin88/Rover-Simulator.git```

The directly runnable script 'rover_swarm_simulation.py' serves as the main function
where the simulation runs and the interface where users can change some settings.

The customizeable settings to the user are introduced below. For any questions, please 
look into the dissertation written by the author Michael Borinuoluwa, supervised by Dr. D. Tarapore, 
"Sparse-swarms: Robot Swarm Co-ordination in Communication Constrained Environment"

## Compiling Rover-Simulator
### Requirements
The simulator requires external libraries which are reccomended to be downloaded into a virtual environment such as Anaconda. The installation commands for all these extra packages are for the Anaconda Prompt a section of the Anaconda software.

To compile and run the sources of Rover-Simulator from Git, the following are needed:

* A Microsoft Windows 10 System (Unix compatability has not been tested yet)
* _numpy_ >= v1.21.2 
  * ```conda install -c anaconda numpy```
 
* _matplotlib_ >= v3.4.3
  * ```conda install -c conda-forge matplotlib```
 
* _pillow_ >= v8.3.1
  * ```conda install -c anaconda pillow```

## Customisable Parameters
All parameters are set at the top of ```rover_swarm_simulation.py```` program.

There are no defaults as these are variables set. So if not changed program runs last configuration.
### Simulation Parameters
Variable | Type | Description
--- | --- | ---
area| STRING | Simulation area (6 letter code from downloaded list)
N | INTEGER | Total rover numbers.
x_offset| INTEGER | Distance from the left boundary which is the location of the first rover. 
y_offset| INTEGER | Distance from the baseline which is the location of the first rover.
goal_offset| INTEGER | Distance to the goal below which the goal is assumed reached. 
steps| INTEGER | Maximum time steps, for the missison.
t_sampling| FLOAT | Simulation Sampling period.
Q| FLOAT ARRAY | The state noise. (Array length of 2 )
R| FLOAT ARRAY | The measurement noise. (Array length of 2 )
ctrl_policy| INTEGER | The control policy used (1, 2, 3, 4).
log_control| STRING | Controls if and what parts of the mission are logged. Treated as a binary string where each bit has control over a different part.
log_step_interval| INTEGER | To reduce data storage size some logs and plots are taken as an average over this interval. (Interval is specified in steps)
log_title_tag| STRING | User specified custom title for the logs.
log_notes| STRING | More detailed notes of a mission taken before running, and is where post mission notes can be added.


### Communication Parameters
Parameters needed to be configured for the LoRa Communication
Variable | Type | Description
--- | --- | ---
user_f| FLOAT | Center frequency of carrier.
user_bw| INTEGER | Bandwidth.
user_sf| INTEGER | Spreading factor.
user_cr| FLOAT | Coding rate.
user_txpw| INTEGER | Transmitting power.
len_interval| FLOAT | Interval between transmissions.


### Line Sweep Parameters
Parameters needed to be configured for a line sweeping mission
Variable | Type | Description
--- | --- | ---
K_goal| FLOAT ARRAY | Gain of controller. 
K_neighbour | FLOAT ARRAY | Gain of controller.
rover_sep| INTEGER | Distance between rovers in meters.
decay| INTEGER | Mathematic style of the decay of rovers speed position, over time. (control policy 2)
zero_crossing| INTEGER | How many time slots the adjustment speed of a neighbouring rover is valid for (control policy 2)


### Advance Line Sweep Parameters
These paramters are needed in addition to the ones stated for line sweep.
Variable | Type | Description
--- | --- | ---
waypoint_interval | INTEGER | Interval for how often to see rover line organisation on plots. (Interval done in steps)
num_of_waypoints| INTEGER | Number of waypoints between starting and proposed end position(including) of each rover.


### Adaptive Sampling
Parameters needed to be configured for an Adaptive Sampling Mission.
Variable | Type | Description
--- | --- | ---
metric_mean| STRING ARRAY | Position of where mean of sampling metric will be located. ([0]: (L)eft, (M)iddle, (R)ight, [1]: (T)op, (M)iddle, (B)ottom)
metric_covariance|2D FLOAT ARRAY | Covariance matrix for generating sampling metric
num_r_samples| INTEGER | Number of base samples to be used if using a fixed sampler. (No. samples adjsuted from this point automatically)
K_sampler[0] | FLOAT | Gain for the rovers own sampling metric measure
K_sampler[1] | FLOAT | Gain for the neighbouring rovers sampling metrics. Affects how significant the neighbouring rovers metrics are.
K_smapler[2] | FLOAT | Gain for natural increase of sampling distance if insignificant metric received. 
sampling_time | INTEGER | Number of steps required for successful sample to be taken. (Steps rover will be stationary for)
metric_order | INTEGER | Whether to take absolute, first order or second order derivative of the metric.
pulse_interval | INTEGER | Interval between transmission that take too long for Duty Cycle Requirements


## Missions
### Line Sweep
The line sweep mission entails the swarm of rovers maintaining a line as they traverse the map. Here each rover only has one goal which is defaulted to directly north of its starting position, at the other end of the map. The controllers available for this type of mission:
* Goal-Driven
  * Controller where the rovers speed is only dependent on the goal.
* Simple Passive
  * Controller where the rover speed is dependent on goal and last received position of neighbouring rovers. 
* Passive
  * Controller where the rover speed is dependent on goal and last received position of neighbouring rovers, where the last received position expires over time.

### Advanced Line Sweep
The advanced line sweep differs from the original line sweep in that the rovers take multiple waypoints between the starting and endpoint, with each of these waypoints being able to be manually adjusted from the user. This allows this line sweep to now avoid certain regions such as water bodies which couldn't be done by the original line sweeping missions. Controllers available for this type of misssion:
* Goal-Driven
  * Controller where the rovers speed is only dependent on the goal.
* Simple Passive
  * Controller where the rover speed is dependent on goal and last received position of neighbouring rovers. 
* Passive
  * Controller where the rover speed is dependent on goal and last received position of neighbouring rovers, where the last received position expires over time.

### Adaptive Sampling
Adaptive sampling is a mission where the swarm ultimately hopes to take samples at the most important points during a sweep to build up an accurate depiction of a distribution of a metric (e.g. greenhoouse gases, temperature...) Controllers available for this type of misssion:
* Independent 
  * Controller changes distance to next sample based on its own measurements.
* Co-operative
  * Controller changes distance to next sample based on its own measurements, and the measurements received from its neighbours.

## LoRa Communication
**Notes:** The communication parameters aren't defaulted to abide to a LoRa Regulations for any particular region, so after running manual check has to be done to see if the LoRa parameters in your region have been abided to. 

After running a mission more details of the LoRa communications are shown such as the duty cycle, this can be found in the ```SSS Parameters.txt``` log file or at the top of ```SSS Summary Data.txt``` or ```SSS Raw Data.txt``` if the mission is from an outdated version of the simulator.

## Maps
### Overview
The maps used in the simulator are generated by data that has to be pre-loaded before the program is run. The 2 types of maps currently used in the program is an elevation, and landcover map.
All elevation and landcover data have the format of ```.asc```. 
Maps added will also have to be in this format. 

### Requirements
To add new landcover maps to the simulator you will need the additionaly package(s) listed below with the following(s) command(s): 
* _gdal_ >= v3.0.2

```conda install -c conda-forge gdal```

### Retrieving New Maps
The elevation data is retrieved from OS Terrain 5 (OS5) grid data which is developed by Ordnance Survey.
The landcover data is retrieved from the Digimap Environment section.
A license is needed to access both.
The data file should be placed in the ```\maps``` directory.

Digimap Link: [https://digimap.edina.ac.uk/](https://digimap.edina.ac.uk/)
#### Terrain
Locate and select the region of choice on Ordnance Survey, then select the OS Terrain 5 DTM option and add to basket, here the format of the file will be prompted to be specified, where the ASC will be the desired option.

#### Landcover
The .tif file is too big to be stored on GitHub so will have to be retrieved manually.
The Environment section of digimap downloads the whole Great Britain, and will have to be subsectioned manually. The website gives the choice of landcover data from different years, the 2020 year has been used here. Within the year option we want the landcover data which has a 25m resolution. Ensure the ```LCM2020_25m.tif``` file is stored in the ```\misc``` directory. And now navigate to this directory via the virtual environment command line and run the following commands:

```gdal_translate -projwin x_left y_top x_right y_bottom LCM2020_25m.tif CMAP.tif```

```gdal_translate -of XYZ -tr 5 5 CMAP.tif CMap.asc```

Manual changes of the parameters in the first of the two commands are needed, these values are integers and can be easily derived from the intial lines of the ascii file of the respective elevation data. See following:

```x_left``` = ```xllcorner```

```y_top``` = ```yllcorner + (nrows * cellsize)``` 

```y_bottom``` = ```yllcorner``` 

```x_right``` = ```xllcorner + (ncols * cellsize)```

Lastly before running the ```lcm_conversion.py``` change the ```the_map``` variable to the correct map name and run the file. The landcover map will be in the correct ```.asc``` format, covering the correct area, and will appear in the ```\maps``` directory.

NOTE: Landcovers are loaded from top left to bottom right, so when we load landcover map columns
and rows are inverted. e.g. if position = (x, y) 
Then if we reference the data directly from the landcover map then we refernce .data(y, x)
However this is already accounted for in the get_data function where easting and northing are swapped. 
Representing this switch the variable names are psuedo_northing, and psuedo_easting
So we can normally call this function as get_data(x, y)

## Logs
Files are logged at the end of mission if desired by the user.
There are multiple files logged after a mission these are as follows:
* ```SSS Raw Data.txt``` - This stores each rovers position, velocity and RMSE of swarm.
* ```SSS Parameters.txt``` - Log file of the parameters selected for mission.
* ```SSS Summary Data.txt``` - Stores a summary of mission.
* ```Elevation.png``` - Plots of the rover trajectories against terrain map.
* ```Landcover.png``` - Plots of the rover trajectories against landcover map.
* ```Mission_Connectivity.png``` - Overall mission connecctivity box plot.
* ```Path_Planned_Trajectory.png``` - Original planned path from user.
* ```RMSE.png``` - Plot of RMSE over time
* ```Velocity.png``` - Plot of magnitude of each rovers velocity as a box plot.
* ```Y_Position.png``` - Line plots of Y position of each rover against time.
* Other plots can be logged as well, and further created in the ```\utils\graphs.py```.
