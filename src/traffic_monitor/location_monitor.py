import carla
import random
import time
import math
import os 
import json
import pandas as pd

# data collection interval
SENSOR_TICK = 3

def get_GNSS_blueprint(world):
    gnss_bp = world.get_blueprint_library().find("sensor.other.gnss")
    gnss_bp.set_attribute('sensor_tick', str(SENSOR_TICK))
    return gnss_bp


def get_lidar_blueprint(world):
    lidar_bp = world.get_blueprint_library().find('sensor.lidar.ray_cast')
    lidar_bp.set_attribute('sensor_tick', str(SENSOR_TICK))
    lidar_bp.set_attribute('channels', '64')
    lidar_bp.set_attribute('points_per_second', '1120000')
    lidar_bp.set_attribute('upper_fov', '30')
    lidar_bp.set_attribute('range', '100')
    lidar_bp.set_attribute('rotation_frequency', '100')
    return lidar_bp


def get_IMU_blueprint(world):
    imu_bp = world.get_blueprint_library().find("sensor.other.imu")
    imu_bp.set_attribute('sensor_tick', str(SENSOR_TICK))
    return imu_bp


def get_speed(vehicle):
    speed = vehicle.get_velocity()
    total_speed = math.sqrt(speed.x**2 + speed.y**2 + speed.z**2)
    return total_speed


def get_GNSS_blueprint(world):
    gnss_bp = world.get_blueprint_library().find("sensor.other.gnss")
    gnss_bp.set_attribute('sensor_tick', str(SENSOR_TICK))
    return gnss_bp


def lidar_callback(data, vehicle):
    file_name = f'sensors/lidar/vehicle-id-{vehicle.id}/frame-{data.frame}.ply'
    data.save_to_disk(file_name)


def gnss_callback_json(data, vehicle):
    file_name = f"sensors/gnss/vehicle-id-{vehicle.id}/frame-{data.frame}.json"

    save_obj = {
        "lat" : data.__getattribute__("latitude"),
        "long" : data.__getattribute__("longitude"),
        "alt" : data.__getattribute__("altitude")
    }

    if not os.path.exists(f"sensors/gnss/vehicle-id-{vehicle.id}/"):
        os.makedirs(f"sensors/gnss/vehicle-id-{vehicle.id}/")

    with open(file_name, 'x') as f:
        json.dump(save_obj, f)

def gnss_callback_csv(data, vehicle):
    file_name = f"sensors/gnss/vehicle-id-{vehicle.id}.csv"

    if not os.path.exists(f"sensors/gnss/"):
        os.makedirs(f"sensors/gnss/")

    save_obj = [{
        "id": vehicle.id,
        "frame": data.frame,
        "timestamp": data.timestamp,
        "lat": data.__getattribute__("latitude"),
        "long": data.__getattribute__("longitude"),
        "alt": data.__getattribute__("altitude"),
        "speed": get_speed(vehicle)
    }]

    if os.path.exists(file_name):
        df = pd.read_csv(file_name)
    else:
        df = None

    df_new_data = pd.DataFrame.from_dict(save_obj)

    if df is None:
        df_new_data.to_csv(file_name, index=False)
    else:
        df = pd.concat([df, df_new_data])
        df.to_csv(file_name, index=False)

client = carla.Client('10.1.5.30', 2000)
client.set_timeout(10.0)

# Load map
world = client.load_world("Town10HD_Opt")

# Get blueprint library and filter only cars
vehicle_blueprints = world.get_blueprint_library().filter('*vehicle*')

# Get maps spawn points
spawn_points = world.get_map().get_spawn_points()

camera_init_trans = carla.Transform(carla.Location(z=1.7))
lidar_init_trans = carla.Transform(carla.Location(z=3.0))

# Create simulation vehicles
vehicle_1 = world.try_spawn_actor(list(vehicle_blueprints)[26], random.choice(spawn_points))
vehicle_2 = world.try_spawn_actor(list(vehicle_blueprints)[26], random.choice(spawn_points))
vehicle_3 = world.try_spawn_actor(list(vehicle_blueprints)[26], random.choice(spawn_points))

# blueprints
lidar_bp = get_lidar_blueprint(world)
gnss_bp = get_GNSS_blueprint(world)
# imu_bp = get_IMU_blueprint(world)

# spawn sensors + attach to vehicles
lidar_1 = world.spawn_actor(lidar_bp, lidar_init_trans, attach_to=vehicle_1)
lidar_2 = world.spawn_actor(lidar_bp, lidar_init_trans, attach_to=vehicle_2)
lidar_3 = world.spawn_actor(lidar_bp, lidar_init_trans, attach_to=vehicle_3)

gnss_1 = world.spawn_actor(gnss_bp, lidar_init_trans, attach_to=vehicle_1)
gnss_2 = world.spawn_actor(gnss_bp, lidar_init_trans, attach_to=vehicle_2)
gnss_3 = world.spawn_actor(gnss_bp, lidar_init_trans, attach_to=vehicle_3)

# set listen action
lidar_1.listen(lambda data: lidar_callback(data, vehicle_1))
lidar_2.listen(lambda data: lidar_callback(data, vehicle_2))
lidar_3.listen(lambda data: lidar_callback(data, vehicle_3))

gnss_1.listen(lambda data: gnss_callback_csv(data, vehicle_1))
gnss_2.listen(lambda data: gnss_callback_csv(data, vehicle_2))
gnss_3.listen(lambda data: gnss_callback_csv(data, vehicle_3))


# Adds vehicles to Traffic manager
vehicle_1.set_autopilot(True)
vehicle_2.set_autopilot(True)
vehicle_3.set_autopilot(True)

spectator = world.get_spectator()
while True:
    transform = lidar_1.get_transform()
    transform.location.z += 1.0
    spectator.set_transform(transform)
    time.sleep(0.004)