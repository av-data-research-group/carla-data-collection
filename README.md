# carla-data-collection
code for data collection and management, using carla simulator

## How to run experiments

1. Navigate to /opt/carla-simulator and start Carla Server 

```console
./CarlaUE4.sh
```

2. Navigate to /opt/carla-simulator/PythonAPI/examples and run "generate traffic"

```console
python generate_traffic.py
```

3. Start AV emulator module in simple mode

```console
python test_sensor_actor.py
```

To run with APM collector, do this instead:

From  the apm folder, bring up elastic APM

```console
docker-compose up
```

Then start the AV emulator with APM client:
```console
python test_sensor_apm.py
```

4. collect CPU + GPU Metrics

```console
pmap [PID] 
ps -o '%cpu' -p [PID]
```

or go to http://localhost:5601/, in case elastic APM is online

pmap -> outputs total memory usage
ps   -> outputs cpu percent usage