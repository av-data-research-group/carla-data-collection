import random
import carla
import datetime
from carla import libcarla, ActorBlueprint, World
import traceback

from pycarlanet import CarlanetActor
from pycarlanet import CarlanetManager
from pycarlanet import CarlanetEventListener, SimulatorStatus

import math
import os
import pandas as pd

AUTO_PILOT = True
NUM_VEHICLES = 0


class B5GCyberTestV2X(CarlanetEventListener):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.carlanet_manager = CarlanetManager(5555, self, log_messages=True)

        self.client = self.sim_world = self.carla_map = None
        self.carlanet_actors = dict()
        self._car = None
        self.remote_agent = RemoteAgent()

    def start_simulation(self):
        self.carlanet_manager.start_simulation()

    def omnet_init_completed(self, run_id, carla_configuration, user_defined) -> (SimulatorStatus, World):
        random.seed(carla_configuration['seed'])

        print(f'OMNeT world is completed with the id {run_id}')
        world = user_defined['carla_world']  # Retrieve from user_defined

        client: libcarla.Client = carla.Client(self.host, self.port)
        client.set_timeout(15)
        sim_world = client.load_world("Town01")
        #sim_world = client.load_world("Town10HD_Opt")
        
        settings = sim_world.get_settings()
        
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None
        settings.no_rendering_mode = False
        settings.fixed_delta_seconds = carla_configuration['carla_timestep']

        #sim_world.set_weather(carla.WeatherParameters.ClearNight)

        sim_world.apply_settings(settings)
        sim_world.tick()
        
        traffic_manager = client.get_trafficmanager()
        traffic_manager.set_synchronous_mode(False)
        traffic_manager.set_random_device_seed(carla_configuration['seed'])
        sim_world.tick()

        client.reload_world(False)  # Reload map keeping the world settings
        #sim_world.set_weather(carla.WeatherParameters.ClearNight)

        sim_world.tick()
        self.client, self.sim_world = client, sim_world
        self.carla_map = self.sim_world.get_map()

        return SimulatorStatus.RUNNING, self.sim_world

    def actor_created(self, actor_id: str, actor_type: str, actor_config) -> CarlanetActor:
        if actor_type == 'car':  # and actor_id == 'car_1':
            blueprint: ActorBlueprint = random.choice(self.sim_world.get_blueprint_library().filter("vehicle.tesla.model3"))

            spawn_points = self.sim_world.get_map().get_spawn_points()
            # Attach sensors
            spawn_point = random.choice(spawn_points)
            print(blueprint)
            response = self.client.apply_batch_sync([carla.command.SpawnActor(blueprint, spawn_point)])[0]
            carla_actor: carla.Vehicle = self.sim_world.get_actor(response.actor_id)

            carla_actor.set_simulate_physics(True)
            if AUTO_PILOT:
                carla_actor.set_autopilot(True)

            carlanet_actor = CarlanetActor(carla_actor, True)
            self.carlanet_actors[actor_id] = carlanet_actor
            self._car = carlanet_actor

            self.vehicle = carla_actor

            self.sim_world.tick()

            #camera_sensor = TeleCarlaCameraSensor(2.2)
            #camera_sensor.attach_to_actor(self.sim_world, carla_actor)
            self.actor_id = actor_id
            
            # send spectator to camera position
            spectator = self.sim_world.get_spectator()
            transform = self.vehicle.get_transform()
            spectator.set_transform(transform)

            if NUM_VEHICLES > 0:
                vehicle_blueprints = self.sim_world.get_blueprint_library().filter('*vehicle*')
                for _ in range(NUM_VEHICLES):
                    npc_vehicle = self.sim_world.try_spawn_actor(list(vehicle_blueprints)[38], random.choice(spawn_points))
                    if npc_vehicle is None:
                        print("vehicle is none")
                    else:
                        npc_vehicle.set_autopilot(True)

            return carlanet_actor
        else:
            raise RuntimeError(f'I don\'t know this type {actor_type}')


    def carla_init_completed(self):
        super().carla_init_completed()

    def before_world_tick(self, timestamp) -> None:
        super().before_world_tick(timestamp)

    def carla_simulation_step(self, timestamp) -> SimulatorStatus:
        self.sim_world.tick()
        # Do all the things, save actors data
        if timestamp > 100:  # ts_limit
            return SimulatorStatus.FINISHED_OK
        else:
            return SimulatorStatus.RUNNING

    # get light control enum from int value
    @staticmethod
    def _str_to_light_control_enum(light_value):
        if light_value == '0':
            return carla.VehicleLightState.NONE
        elif light_value == '1':
            return carla.VehicleLightState.Position
        elif light_value == '2':
            return carla.VehicleLightState.Brake
        else:
            return carla.VehicleLightState.All
        
    # get int value from light control enum
    @staticmethod
    def _light_control_enum_to_str(light_enum):
        if light_enum == carla.VehicleLightState.NONE:
            return '0'
        elif light_enum == carla.VehicleLightState.Position:
            return '1'
        elif light_enum == carla.VehicleLightState.Brake:
            return '2'
        else:
            return '3'
        
    

    
    def generic_message(self, timestamp, user_defined_message) -> (SimulatorStatus, dict):
        # Handle the action of the actors in the world (apply_commands, calc_instruction)
        # es: apply_commands with id command_12 to actor with id active_actor_14
        if user_defined_message['msg_type'] == 'LIGHT_COMMAND':
            #actor_id = user_defined_message['actor_id']
            #self.carlanet_actors[actor_id].set_light_state(user_defined_message['light_next_state'])
            
            #convert enum value to enum
            next_light_state = self._str_to_light_control_enum(user_defined_message['light_next_state'])
            self._car.set_light_state(next_light_state)

            msg_to_send = {'msg_type': 'LIGHT_UPDATE',
                           'light_curr_state': self._light_control_enum_to_str(self._car.get_light_state())}
            
            print("LIGHT CURR STATE: ", self._car.get_light_state(), '\n\n')
            return SimulatorStatus.RUNNING, msg_to_send
        
        elif user_defined_message['msg_type'] == 'LIGHT_UPDATE':
            curr_light_state = self._str_to_light_control_enum(user_defined_message['light_curr_state'])
            next_light_state = self.remote_agent.calc_next_light_state(curr_light_state)
            print("LIGHT CURR STATE: ", curr_light_state, "LIGHT NEXT STATE: ", next_light_state, '\n')

            msg_to_send = {'msg_type': 'LIGHT_COMMAND',
                           'light_next_state': self._light_control_enum_to_str(next_light_state)
                           }
            
            # GET locations and save it to csv
            print("#" * 50)
            print("getting sensor data from car")
            self.remote_agent.process_vehicle_data(self.vehicle, self.carlanet_manager)

            ### CONTROL STAGE
            if not AUTO_PILOT:
                pass

            # send spectator to camera position
            spectator = self.sim_world.get_spectator()
            transform = self.vehicle.get_transform()
            spectator.set_transform(transform)

            return SimulatorStatus.RUNNING, msg_to_send
        else:
            raise RuntimeError(f"I don\'t know this type {user_defined_message['msg_type']}")

    def simulation_finished(self, status_code: SimulatorStatus):
        super().simulation_finished(status_code)

    def simulation_error(self, exception):
        traceback.print_exc()
        super().simulation_error(exception)


class RemoteAgent:

    def __init__(self):
        self.light_state = carla.VehicleLightState.NONE

    def calc_next_light_state(self, light_state: carla.VehicleLightState):
        return carla.VehicleLightState.NONE
    
    def process_vehicle_data(vehicle, carlanet_manager):
        file_name = f"sensors_high_traffic/gnss/vehicle-id-{vehicle.id}.csv"

        if not os.path.exists(f"sensors_high_traffic/gnss/"):
            os.makedirs(f"sensors_high_traffic/gnss/")

        positions_obj = carlanet_manager._generate_carla_nodes_positions()[0]
        x_speed = positions_obj["velocity"][0]
        y_speed = positions_obj["velocity"][1]
        z_speed = positions_obj["velocity"][2]
        speed = math.sqrt(x_speed**2 + y_speed**2 + z_speed**2)
        current_time = datetime.datetime.now()

        save_obj = [{
            "id": vehicle.id,
            "timestamp": str(current_time),
            "lat": positions_obj["position"][0],
            "long": positions_obj["position"][1],
            "alt": positions_obj["position"][2],
            "speed": speed
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


if __name__ == '__main__':
    my_world = B5GCyberTestV2X('localhost', 2000)
    my_world.start_simulation()
