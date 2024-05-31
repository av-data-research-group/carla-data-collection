SENSOR_TICK = 3

def get_cam_blueprint(world):
    cam_bp = world.get_blueprint_library().find("sensor.camera.rgb")
    cam_bp.set_attribute("image_size_x", str(400))
    cam_bp.set_attribute("image_size_y", str(300))
    cam_bp.set_attribute("fov", str(100))
    cam_bp.set_attribute("sensor_tick", str(SENSOR_TICK))
    return cam_bp
