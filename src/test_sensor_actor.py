import glob
import os
import sys
import time


try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import argparse
import logging
import random

def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    args = argparser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    client = carla.Client(args.host, args.port)
    client.set_timeout(10.0)

    try:

        world = client.get_world()
        ego_vehicle = None
        ego_cam = None
        ego_col = None
        ego_lane = None
        ego_obs = None
        ego_gnss = None
        ego_imu = None

        # --------------
        # Start recording
        # --------------
        
        client.start_recorder('recorder/recording01.log')
        

        # --------------
        # Spawn ego vehicle
        # --------------
        
        ego_bp = world.get_blueprint_library().find('vehicle.tesla.model3')
        ego_bp.set_attribute('role_name','ego')
        print('\nEgo role_name is set')
        ego_color = random.choice(ego_bp.get_attribute('color').recommended_values)
        ego_bp.set_attribute('color',ego_color)
        print('\nEgo color is set')

        spawn_points = world.get_map().get_spawn_points()
        number_of_spawn_points = len(spawn_points)

        if 0 < number_of_spawn_points:
            random.shuffle(spawn_points)
            ego_transform = spawn_points[0]
            ego_vehicle = world.spawn_actor(ego_bp,ego_transform)
            print('\nEgo is spawned')
        else: 
            logging.warning('Could not found any spawn points')
        

        # --------------
        # Add a RGB camera sensor to ego vehicle. 
        # --------------
        
        cam_bp = None
        cam_bp = world.get_blueprint_library().find('sensor.camera.rgb')
        cam_bp.set_attribute("image_size_x",str(1920))
        cam_bp.set_attribute("image_size_y",str(1080))
        cam_bp.set_attribute("fov",str(105))
        cam_bp.set_attribute("sensor_tick",str(3))
        cam_location = carla.Location(-2,0,3)
        cam_rotation = carla.Rotation(0,0,0)
        cam_transform = carla.Transform(cam_location,cam_rotation)
        ego_cam = world.spawn_actor(cam_bp,cam_transform,attach_to=ego_vehicle, attachment_type=carla.AttachmentType.Rigid)
        # ego_cam.listen(lambda image: image.save_to_disk(f"output/camera/{image.frame}.jpg"))
        

        # --------------
        # Add collision sensor to ego vehicle. 
        # --------------
        collision_log_file = "output/recorder/collision_log.txt"

        col_bp = world.get_blueprint_library().find('sensor.other.collision')
        col_location = carla.Location(0,0,0)
        col_rotation = carla.Rotation(0,0,0)
        col_transform = carla.Transform(col_location,col_rotation)
        ego_col = world.spawn_actor(col_bp,col_transform,attach_to=ego_vehicle, attachment_type=carla.AttachmentType.Rigid)
        def col_callback(colli):
            print("Collision detected:\n"+str(colli)+'\n')
            # with open(collision_log_file, "a") as collision_file_object:
            #     collision_file_object.write("Collision warning:\n"+str(colli)+'\n')
        ego_col.listen(lambda colli: col_callback(colli))
        

        # --------------
        # Add Lane invasion sensor to ego vehicle. 
        # --------------
        lane_log_file = "output/recorder/lane_log.txt"
        

        lane_bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        lane_location = carla.Location(0,0,0)
        lane_rotation = carla.Rotation(0,0,0)
        lane_transform = carla.Transform(lane_location,lane_rotation)
        ego_lane = world.spawn_actor(lane_bp,lane_transform,attach_to=ego_vehicle, attachment_type=carla.AttachmentType.Rigid)
        def lane_callback(lane):
            print("Lane invasion detected:\n"+str(lane)+'\n')
            # with open(lane_log_file, "a") as lane_file_object:
            #    lane_file_object.write("Lane invasion detected:\n"+str(lane)+'\n')

        ego_lane.listen(lambda lane: lane_callback(lane))
        

        # --------------
        # Add Obstacle sensor to ego vehicle. 
        # --------------
        obstacle_log_file = "output/recorder/obstacle_log.txt"

        obs_bp = world.get_blueprint_library().find('sensor.other.obstacle')
        obs_bp.set_attribute("only_dynamics",str(True))
        obs_location = carla.Location(0,0,0)
        obs_rotation = carla.Rotation(0,0,0)
        obs_transform = carla.Transform(obs_location,obs_rotation)
        ego_obs = world.spawn_actor(obs_bp,obs_transform,attach_to=ego_vehicle, attachment_type=carla.AttachmentType.Rigid)
        def obs_callback(obs):
            print("Obstacle detected:\n"+str(obs)+'\n')
            # with open(obstacle_log_file, "a") as obstacle_file_object:
            #     obstacle_file_object.write("Obstacle detected:\n"+str(obs)+'\n')
        ego_obs.listen(lambda obs: obs_callback(obs))
        
        # --------------
        # Place spectator on ego spawning
        # --------------
        
        spectator = world.get_spectator()
        world_snapshot = world.wait_for_tick() 
        #spectator.set_transform(ego_vehicle.get_transform())
        

        # --------------
        # Enable autopilot for ego vehicle
        # --------------
        
        ego_vehicle.set_autopilot(True)
        
        
        # --------------
        # Game loop. Prevents the script from finishing.
        # --------------
        while True:
            world_snapshot = world.wait_for_tick()
            
            location = ego_vehicle.get_transform().location
            rotation = ego_vehicle.get_transform().rotation
            new_transform = carla.Transform(location, rotation)
            new_transform.location.x -= 1
            new_transform.location.z += 5

            new_transform.location.y -= 6
            #print(new_transform.rotation)

            #spectator.set_transform(new_transform)
            spectator.set_transform(carla.Transform(ego_vehicle.get_transform().location + carla.Location(z=5,y=-2,x=-2),
            rotation)) #yaw=90, roll=-90

    finally:
        # --------------
        # Stop recording and destroy actors
        # --------------
        client.stop_recorder()
        if ego_vehicle is not None:
            if ego_cam is not None:
                ego_cam.stop()
                ego_cam.destroy()
            if ego_col is not None:
                ego_col.stop()
                ego_col.destroy()
            if ego_lane is not None:
                ego_lane.stop()
                ego_lane.destroy()
            if ego_obs is not None:
                ego_obs.stop()
                ego_obs.destroy()
            if ego_gnss is not None:
                ego_gnss.stop()
                ego_gnss.destroy()
            if ego_imu is not None:
                ego_imu.stop()
                ego_imu.destroy()
            ego_vehicle.destroy()

if __name__ == '__main__':

    try:
        main()
        
    except KeyboardInterrupt:
        pass
        
    finally:
        print('\nEnd of the experiment.')



