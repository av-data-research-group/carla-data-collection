#!/usr/bin/env python
# coding: utf-8

import carla
import random
import re
import time


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
    cam_bp.set_attribute("image_size_x",str(400))
    cam_bp.set_attribute("image_size_y",str(300))
    cam_bp.set_attribute("fov",str(100))
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

camera_1_init_trans = carla.Transform(carla.Location(z=2.3))
camera_2_init_trans = carla.Transform(carla.Location(z=2.3), carla.Rotation(yaw=180))
lidar_init_trans = carla.Transform(carla.Location(z=3.0))

# creates camera and attaches it to the vehicle
camera_1_bp = get_cam_blueprint(world)
camera_2_bp = get_cam_blueprint(world)
camera_1 = world.spawn_actor(camera_1_bp, camera_1_init_trans, attach_to=vehicle)
camera_2 = world.spawn_actor(camera_2_bp, camera_2_init_trans, attach_to=vehicle)
camera_1.listen(lambda image: image.save_to_disk(f"sensors/camera_1/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_2.listen(lambda image: image.save_to_disk(f"sensors/camera_2/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))

# creates lidar and attaches it to the vehicle
lidar_bp = get_lidar_blueprint(world)
lidar = world.spawn_actor(lidar_bp, lidar_init_trans, attach_to=vehicle)
lidar.listen(lambda data: data.save_to_disk(f'sensors/lidar/vehicle-id-{vehicle.id}-frame-{data.frame}.ply'))

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