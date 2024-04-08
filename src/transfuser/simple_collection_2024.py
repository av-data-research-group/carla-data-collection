#!/usr/bin/env python
# coding: utf-8

import carla
import random
import json
import time
import math
import os
import inspect
### Client

#client = carla.Client('localhost', 2000)
client = carla.Client('10.1.5.81', 2000)
client.set_timeout(10.0)
world = client.get_world()

# world.__dir__()
for map_name in client.get_available_maps():
    print(map_name)
world.get_map().name

# Load map
world = client.load_world("Town10HD_Opt")

# Get blueprint library and filter only cars
vehicle_blueprints = world.get_blueprint_library().filter('*vehicle*')
for idx, blueprint in enumerate(vehicle_blueprints):
    print(idx, blueprint.id)
    if idx == 10:
        break

### Add vehicle to world

# Get maps spawn points
spawn_points = world.get_map().get_spawn_points()

# Tesla Cybertruck
vehicle = world.try_spawn_actor(list(vehicle_blueprints)[26], random.choice(spawn_points))
print(vehicle)

vehicle_transform = vehicle.get_transform()
vehicle_transform.location.z += 2.0
world.get_spectator().set_transform(vehicle_transform)

### Add sensors to car

# time in seconds to collect data
SENSOR_TICK = 3

def get_cam_blueprint(world):
    cam_bp = world.get_blueprint_library().find('sensor.camera.rgb')
    cam_bp.set_attribute("image_size_x",str(960))
    cam_bp.set_attribute("image_size_y",str(480))
    cam_bp.set_attribute("fov",str(120))
    cam_bp.set_attribute("sensor_tick",str(SENSOR_TICK))
    return cam_bp


def get_lidar_blueprint(world):
    lidar_bp = world.get_blueprint_library().find('sensor.lidar.ray_cast')
    lidar_bp.set_attribute('sensor_tick', str(SENSOR_TICK))
    lidar_bp.set_attribute('channels', '64')
    lidar_bp.set_attribute('points_per_second', '1120000')
    lidar_bp.set_attribute('upper_fov', '30')
    lidar_bp.set_attribute('range', '100')
    lidar_bp.set_attribute('rotation_frequency', '100')
    return lidar_bp

def get_GNSS_blueprint(world):
    gnss_bp = world.get_blueprint_library().find("sensor.other.gnss")
    gnss_bp.set_attribute('sensor_tick', str(SENSOR_TICK))
    return gnss_bp

def get_IMU_blueprint(world):
    imu_bp = world.get_blueprint_library().find("sensor.other.imu")
    imu_bp.set_attribute('sensor_tick', str(SENSOR_TICK))
    return imu_bp

def get_speedometer(vehicle):
    speed = vehicle.get_velocity()
    total_speed = math.sqrt(speed.x**2 + speed.y**2 + speed.z**2)
    return total_speed


camera_1_init_trans = carla.Transform(carla.Location(z=2.3))
camera_2_init_trans = carla.Transform(carla.Location(z=2.3), carla.Rotation(yaw=-60))
camera_3_init_trans = carla.Transform(carla.Location(z=2.3), carla.Rotation(yaw=60))
lidar_init_trans = carla.Transform(carla.Location(z=3.0))

# creates camera and attaches it to the vehicle
camera_1_bp = get_cam_blueprint(world)
camera_2_bp = get_cam_blueprint(world)
camera_3_bp = get_cam_blueprint(world)
camera_1 = world.spawn_actor(camera_1_bp, camera_1_init_trans, attach_to=vehicle)
camera_2 = world.spawn_actor(camera_2_bp, camera_2_init_trans, attach_to=vehicle)
camera_3 = world.spawn_actor(camera_3_bp, camera_3_init_trans, attach_to=vehicle)
camera_1.listen(lambda image: image.save_to_disk(f"sensors/camera_1/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_2.listen(lambda image: image.save_to_disk(f"sensors/camera_2/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_3.listen(lambda image: image.save_to_disk(f"sensors/camera_3/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))

# creates lidar and attaches it to the vehicle
lidar_bp = get_lidar_blueprint(world)
lidar = world.spawn_actor(lidar_bp, lidar_init_trans, attach_to=vehicle)
lidar.listen(lambda data: data.save_to_disk(f'sensors/lidar/vehicle-id-{vehicle.id}-frame-{data.frame}.ply'))

def gnss_callback(data):
    file_name = f"sensors/gnss/vehicle-id-{vehicle.id}-frame-{data.frame}.json"

    save_obj = {
        "lat" : data.__getattribute__("latitude"),
        "long" : data.__getattribute__("longitude"),
        "alt" : data.__getattribute__("altitude")
    }

    if not os.path.exists("sensors/gnss/"):
        os.makedirs("sensors/gnss/")

    with open(file_name, 'x') as f:
        json.dump(save_obj, f)

def imu_callback(data):
    file_name = f"sensors/imu/vehicle-id-{vehicle.id}-frame-{data.frame}.json"

    accelerometer = data.__getattribute__("accelerometer")
    accelerometer = {
        "x": accelerometer.x,
        "y": accelerometer.y,
        "z": accelerometer.z,
    }

    gyroscope = data.__getattribute__("gyroscope")
    gyroscope = {
        "x": gyroscope.x,
        "y": gyroscope.y,
        "z": gyroscope.z,
    }

    compass = data.__getattribute__("compass")

    save_obj = {
        "accelerometer" : accelerometer,
        "gyroscope" : gyroscope,
        "compass" : compass
    }

    if not os.path.exists("sensors/imu/"):
        os.makedirs("sensors/imu/")

    with open(file_name, 'x') as f:
        json.dump(save_obj, f)

# creates GNSS and attaches it to vehicle
gnss_bp = get_GNSS_blueprint(world)
gnss = world.spawn_actor(gnss_bp, lidar_init_trans, attach_to=vehicle)
gnss.listen(lambda data: gnss_callback(data))

# creates IMU and attaches it to vehicle
imu_bp = get_IMU_blueprint(world)
imu = world.spawn_actor(imu_bp, lidar_init_trans, attach_to=vehicle)
imu.listen(lambda data:imu_callback(data))

# Adds vehicle to Traffic manager
vehicle.set_autopilot(True)

# Faz o spectator seguir o carro
spectator = world.get_spectator()
while True:
    transform = camera_1.get_transform()
    transform.location.z += 2.0
    spectator.set_transform(transform)
    time.sleep(0.004)

# Remove o carro da simulação
vehicle.destroy()