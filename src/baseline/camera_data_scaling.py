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
client = carla.Client('10.1.5.30', 2000)
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
CAMERAS = 9
CAMERAS_YAW = [-80,-60,-40,-20,0,20,40,60,80]

def get_cam_blueprint(world):
    cam_bp = world.get_blueprint_library().find('sensor.camera.rgb')
    cam_bp.set_attribute("image_size_x",str(960))
    cam_bp.set_attribute("image_size_y",str(480))
    cam_bp.set_attribute("fov",str(120))
    cam_bp.set_attribute("sensor_tick",str(SENSOR_TICK))
    return cam_bp

camera_list = []

for i in range(CAMERAS):
    camera_init_trans = carla.Transform(
        carla.Location(z=2.3),
        carla.Rotation(yaw=CAMERAS_YAW[i])
    )
    cam_id = str(i+1)
    # creates camera and attaches it to the vehicle
    camera_bp = get_cam_blueprint(world)
    camera = world.spawn_actor(camera_bp, camera_init_trans, attach_to=vehicle)
    camera_list.append(camera)

camera_list[0].listen(lambda image: image.save_to_disk(f"sensors/camera_{1}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[1].listen(lambda image: image.save_to_disk(f"sensors/camera_{2}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[2].listen(lambda image: image.save_to_disk(f"sensors/camera_{3}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[3].listen(lambda image: image.save_to_disk(f"sensors/camera_{4}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[4].listen(lambda image: image.save_to_disk(f"sensors/camera_{5}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[5].listen(lambda image: image.save_to_disk(f"sensors/camera_{6}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[6].listen(lambda image: image.save_to_disk(f"sensors/camera_{7}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[7].listen(lambda image: image.save_to_disk(f"sensors/camera_{8}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))
camera_list[8].listen(lambda image: image.save_to_disk(f"sensors/camera_{9}/vehicle-id-{vehicle.id}-frame-{image.frame}.png"))

# Adds vehicle to Traffic manager
vehicle.set_autopilot(True)

# Faz o spectator seguir o carro
spectator = world.get_spectator()
while True:
    transform = vehicle.get_transform()
    transform.location.z += 2.0
    spectator.set_transform(transform)
    time.sleep(0.004)

# Remove o carro da simulação
vehicle.destroy()