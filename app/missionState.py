from GUI import GUI
from Dispatcher import Dispatcher
import asyncio
import threading
from TerrainPreProcessing.terrain_queries import create_search_area
from TerrainPreProcessing.visualization import plot_search_area

class Drone:
    drone_id = None
    system_status = None
    latitude = None # Note: this is not a float, it is a int with 7 decimal places
    longitude = None # Note: this is not a float, it is a int with 7 decimal places
    altitude = None # millimeters above sea level
    relative_altitude = None # millimeters above home
    heading = None # degrees
    vx = None # cm per second
    vy = None # cm per second
    vz = None # cm per second

    def __init__(self, missionState, drone_id, system_status):
        self.missionState = missionState
        self.drone_id = drone_id
        self.system_status = system_status

    #SETTERS
    def updatePosition(self, latitude, longitude, altitude, relative_altitude, heading, vx, vy, vz):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.relative_altitude = relative_altitude
        self.heading = heading
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.missionState.gui.updateDronePosition(self.drone_id, latitude, longitude, altitude, relative_altitude, heading, vx, vy, vz)

    
    def updateTelemetry(self, roll, pitch, yaw):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
        self.missionState.gui.updateDroneTelemetry(self.drone_id, roll, pitch, yaw)
    def updateStatus(self, system_status):
        self.system_status = system_status
        self.missionState.gui.updateDroneStatus(self.drone_id, system_status)
    
class Job:
    def __init__(self, job_id, job_type, job_status, waypoints, missionState, drone_id):
        self.missionState = missionState
        self.drone_id = drone_id
        self.job_id = job_id
        self.job_type = job_type
        self.job_status = job_status
        self.waypoints = waypoints
        self.last_waypoint = 0
    
    def deployJob(self):
        self.job_status = "deployed"
        if self.job_type == "INVESTIGATE_POI":
            self.last_waypoint = 0
            self.missionState.send_poi_investigate(self.drone_id, self.waypoints[0])


class missionState:

    def __init__(self, gui):
        self.drones = []
        self.missionPolygon = None
        self.mavLinkConnected = False
        self.gui = gui
        self.loop = asyncio.new_event_loop()
        self.dispatcher = Dispatcher.Dispatcher(self)
        # TEST VALUES
        self.mission_waypoints = [(28.6013158, -81.2020057, 10, 0 ), (28.6031200, -81.1993369, 10, 0) , (28.6004825, -81.1942729, 10, 0)]
        
        
    def connect_to_mavlink(self):
        success = self.dispatcher.connect()
        if success:
            self.dispatcherThread = threading.Thread(target=self.run_asyncio_loop, daemon=True)
            self.dispatcherThread.start()
            self.mavLinkConnected = True
            print("Connected to MAVLink")
        else:
            print("Failed to connect to MAVLink")
            self.mavLinkConnected = False

    
    def run_asyncio_loop(self):
        """Runs the asyncio event loop in a separate thread for the dispatcher."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.dispatcher.receive_packets())

    def addDrone(self, drone_id, system_status):
        self.drones.append(Drone(self, drone_id, system_status))
        self.drones.sort(key=lambda x: x.drone_id)
        self.gui.addDrone(drone_id, system_status)

    def updateDronePosition(self, drone_id, latitude, longitude, altitude, relative_altitude, heading, vx, vy, vz):
        drone = next((d for d in self.drones if d.drone_id == drone_id), None)
        if drone is not None:
            drone.updatePosition(latitude, longitude, altitude, relative_altitude, heading, vx, vy, vz)

    def updateDroneTelemetry(self, drone_id, roll, pitch, yaw):
        drone = next((d for d in self.drones if d.drone_id == drone_id), None)
        if drone is not None:
            drone.updateTelemetry(roll, pitch, yaw)

    def addMissionPolygon(self, polygon):
        print("Gotcha!")
        print(polygon)
        rtree, grid = create_search_area(polygon_points=polygon, search_tags={"building":True,"water":True}, useOSMX=True, maximum_square_size=60,minimum_grid_size=8)
        plot_search_area(rtree,grid, polygon)
        self.missionGrid = grid
        self.rtree = rtree
        self.missionPolygon = polygon

    def getMissionPolygon(self):
        return self.missionPolygon

    def updateDroneStatus(self, drone_id, system_status):
        # check if drone exists yet 
        drone = next((d for d in self.drones if d.drone_id == drone_id), None)
        if drone is None:
            self.addDrone(drone_id, system_status)
        else:
            drone.updateStatus(system_status)
    
    def getDrones(self):
        return self.drones
    
    def get_drone(self, drone_id):
        return next((d for d in self.drones if d.drone_id == drone_id), None)

    def arm_mission(self, drone_id):
        self.dispatcher.arm_drone(drone_id)
    
    def takeoff_mission(self, drone_id):
        self.dispatcher.takeoff_drone(drone_id)
    
    def send_waypoints(self, drone_id):
        self.dispatcher.send_mission(drone_id, self.mission_waypoints)
    
    def return_to_launch(self, drone_id):
        self.dispatcher.return_to_launch(drone_id)
    
    def send_poi_investigate(self, drone_id, waypoint):
        self.dispatcher.send_poi_investigate(drone_id, waypoint)
        
    
if __name__ == "__main__":
    gui = GUI.GUI()
    missionState = missionState(gui)
    gui.link_mission_state(missionState)
    gui.run()
    

    




    