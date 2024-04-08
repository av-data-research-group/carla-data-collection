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

# Adds vehicle to Traffic manager
vehicle.set_autopilot(True)

# Faz o spectator seguir o carro
spectator = world.get_spectator()
while True:
    transform = vehicle.get_transform()
    transform.location.z += 3.0
    spectator.set_transform(transform)
    time.sleep(0.004)

# Remove o carro da simulação
vehicle.destroy()