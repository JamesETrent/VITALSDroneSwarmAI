
from pymavlink import mavutil
import asyncio
import threading
import time
import math

class mission_item:
    def __init__(self, seq, current, lat, lon, alt):
        self.seq = seq
        self.frame = mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT
        self.command = mavutil.mavlink.MAV_CMD_NAV_WAYPOINT
        self.current = current
        self.auto = 1
        self.param1 = 0.0
        self.param2 = 2.0
        self.param3 = 0
        self.param4 = 0.0
        self.lat = int(1e7 * lat)
        self.lon = int(1e7 * lon)
        self.alt = alt


class Dispatcher:
    def __init__(self, missionState):
        self.master = None
        self.missionState = missionState
        self.uploading_missions = {}
        
    def connect(self):
        try:
            self.master = mavutil.mavlink_connection('tcp:127.0.0.1:14550', mavlink_version="2.0")
            self.master.wait_heartbeat()
            print("Connected to MAVLink")
            return True
        except Exception as e:
            print(f"Error connecting to MAVLink: {e}")
            self.master = None
            return False
    

    async def receive_packets(self):
        """Continuously process MAVLink messages with minimal latency."""
        if not self.master:
            print("No MAVLink connection established.")
            return

        try:
            while True:
                # Process ALL available messages before sleeping
                messages_processed = 0
                
                while True:
                    msg = self.master.recv_match(blocking=False)
                    if not msg:
                        break  # No more messages, exit loop

                    messages_processed += 1
                    drone_id = msg.get_srcSystem()
                    msg_type = msg.get_type()

                    if msg_type == "HEARTBEAT":
                        self.missionState.updateDroneStatus(drone_id, msg.system_status)

                    elif msg_type == "GLOBAL_POSITION_INT":
                        self.missionState.updateDronePosition(
                            drone_id, msg.lat, msg.lon, msg.alt, msg.relative_alt,
                            msg.hdg, msg.vx, msg.vy, msg.vz
                        )

                    elif msg_type == "ATTITUDE":
                        self.missionState.updateDroneTelemetry(
                            drone_id, msg.roll, msg.pitch, msg.yaw
                        )
                    elif msg_type == "MISSION_REQUEST":
                            print(f"Received mission request {msg.seq} from drone {drone_id}")
                            await self.handle_mission_request(drone_id, msg.seq)

                    elif msg_type == "MISSION_ACK":
                            await self.handle_mission_ack(drone_id, msg.type)

                    elif msg_type == "COMMAND_ACK":
                            print(f"Command acknowledgment received for drone {drone_id}: {msg.command} - {msg.result}")
                    elif msg_type == "MISSION_ITEM_REACHED":
                            print(f"Drone {drone_id} reached waypoint {msg.seq}")


                if messages_processed == 0:
                    await asyncio.sleep(0.001)  # Only sleep if no messages were processed

        except Exception as e:
            print(f"Dispatcher error: {e}")
        finally:
            if self.master:
                self.master.close()

    def clear_mission(self, drone_id):
        self.master.target_system = drone_id
        self.master.waypoint_clear_all_send()
    
    def arm_drone(self, drone_id):
        print(f"Arming drone {drone_id}")
        print(f"target_component: {self.master.target_component}")
        self.master.target_system = drone_id
        self.master.set_mode(216)
        self.master.arducopter_arm()
    
    def send_mission(self, drone_id, waypoints):
        """Upload mission waypoints for a specific drone in a separate thread."""
        if not self.master:
            print(f"Cannot upload waypoints: MAVLink is not connected!")
            return

        def mission_thread():
            asyncio.run(self.upload_mission(drone_id, waypoints))

        threading.Thread(target=mission_thread, daemon=True).start()  # Start in a new thread

    async def upload_mission(self, drone_id, waypoints):
        """Initiate mission upload using the correct MAVLink protocol."""

        # Get the drone's current status
        drone = self.missionState.get_drone(drone_id)
        if not drone:
            print(f"Drone {drone_id} not found.")
            return
        if drone.system_status == 3 : #drone is grounded need to add takeoff
            waypoints.insert(0, (drone.latitude, drone.longitude, 10, 1))
            

        # Clear existing mission
        self.master.mav.mission_clear_all_send(drone_id, 0)
        await asyncio.sleep(1)  # Allow time for clearing

        # Send mission count
        mission_count = len(waypoints)
        print(f"Sending MISSION_COUNT for {mission_count} waypoints to drone {drone_id}")
        
        self.master.mav.mission_count_send(drone_id, 0, mission_count)
        await asyncio.sleep(2)  # Allow drone time to process

        #Wait for mission requests and respond accordingly
        self.uploading_missions[drone_id] = {
            "waypoints": waypoints,
            "next_seq": 0,
            "waiting_for_request": True
        }


    async def handle_mission_request(self, drone_id, seq):
        """Respond to mission requests from the drone."""
        mission = self.uploading_missions.get(drone_id)
        print(f"Received mission request {seq} from drone {drone_id}")

        if mission and seq < len(mission["waypoints"]):
            lat, lon, alt, type = mission["waypoints"][seq]
            self.send_waypoint(drone_id, seq, lat, lon, alt, type)
            mission["next_seq"] = seq + 1
            mission["waiting_for_request"] = False
        else:
            print(f"Received unexpected mission request {seq} from drone {drone_id}")

    def send_waypoint(self, drone_id, index, lat, lon, alt, waypoint_type=0):
        """Send a specific waypoint in response to a mission request."""
        
        print(f"Sending waypoint {index} to drone {drone_id}: {lat}, {lon}, {alt}")
        if waypoint_type == 0: # Normal Waypoint
            self.master.mav.mission_item_int_send(
                drone_id,  # Target drone
                0,  # Target component
                index,  # Waypoint index
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                0,  # Current waypoint flag
                1,  # Auto-continue
                0, 2.0, 0, 0,  # Empty params
                int(lat * 1e7), int(lon * 1e7), alt
            )
            print(f"Waypoint {index} sent to drone {drone_id}: {lat}, {lon}, {alt}")
        elif waypoint_type == 1: # Takeoff Command
            self.master.mav.mission_item_int_send(
                drone_id,  # Target drone
                0,  # Target component
                index,  # Waypoint index
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
                0,  # Current waypoint flag
                1,  # Auto-continue
                0,  # pitch
                0, 0,  # Empty params
                0, #yaw
                lat, lon, alt
            )
            print(f"Waypoint {index} sent to drone {drone_id}: {lat}, {lon}, {alt}")
        elif waypoint_type == 2: # Loiter turns Command
            self.master.mav.mission_item_int_send(
                drone_id,  # Target drone
                0,  # Target component
                index,  # Waypoint index
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                mavutil.mavlink.MAV_CMD_NAV_LOITER_TURNS,
                0,  # Current waypoint flag
                1,  # Auto-continue
                3,  # Number of turns
                0,  # Heading
                12, #Radius (m)
                0,  #NA for copters
                int(lat * 1e7), int(lon * 1e7), alt
            )
            print(f"Waypoint {index} sent to drone {drone_id}: {lat}, {lon}, {alt}")


    async def handle_mission_ack(self, drone_id, ack_type):
        """Handle final mission acknowledgment."""
        if ack_type == mavutil.mavlink.MAV_MISSION_ACCEPTED:
            print(f"Mission upload to drone {drone_id} completed successfully!")
            self.start_mission(drone_id)
        else:
            print(f"Mission upload failed for drone {drone_id} with error code {ack_type}")

    def start_mission(self, drone_id):
        """Start the mission for a specific drone."""


        #arm drone
        self.master.mav.command_long_send(
                drone_id,  # target_system
                0,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, # command
                0, # confirmation
                1, # param1 (1 to indicate arm)
                21196, #  FORCE ARM for testing
                0, # param3
                0, # param4
                0, # param5
                0, # param6
                0) # param7
        
        self.ack("COMMAND_ACK")
        self.master.mav.set_mode_send(
            drone_id,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            3  # AUTO mode (ArduPilot)
        )
       
        self.master.mav.command_long_send(
            drone_id,
            0,  # Target component
            mavutil.mavlink.MAV_CMD_MISSION_START,
            0,  # Confirmation
            0, 0, 0, 0, 0, 0, 0
        )
        
        print(f"Mission started for drone {drone_id} in AUTO mode.")
    
    def set_mode(self, drone_id, mode):
        """Set the flight mode of the drone before takeoff."""
        if not self.master:
            print(f"Cannot set mode: MAVLink is not connected!")
            return

        mode_mapping = {
            "GUIDED": 4,
            "AUTO": 3,
            "LOITER": 5,
            "RTL": 6
        }

        if mode not in mode_mapping:
            print(f"Invalid mode: {mode}")
            return

        print(f"Setting drone {drone_id} mode to {mode}...")

        self.master.mav.set_mode_send(
            drone_id,
            mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
            mode_mapping[mode]
        )
    async def wait_for_arming(self, drone_id, timeout=10):
        """Wait until the drone is armed before continuing."""
        print(f"Waiting for drone {drone_id} to arm...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            msg = self.master.recv_match(type="HEARTBEAT", blocking=False)
            if msg and msg.get_srcSystem() == drone_id:
                if msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
                    print(f"Drone {drone_id} is now armed!")
                    return
            await asyncio.sleep(0.5)  # Check every 0.5s

        print(f"Warning: Drone {drone_id} did not arm within timeout!")
    
    def takeoff_drone(self, drone_id, altitude=10):
        """Set mode to GUIDED and send a takeoff command."""
        if not self.master:
            print(f"Cannot take off: MAVLink is not connected!")
            return

        # Step 1: Set mode to GUIDED
        self.set_mode(drone_id, "GUIDED")
        print(f"Drone {drone_id} switched to GUIDED mode.")

        # Step 2: Send ARM command
        print(f"Arming drone {drone_id}...")
        self.master.mav.command_long_send(
            drone_id,
            0,  # Target component
            mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            0,  # Confirmation
            1,  # 1 = Arm, 0 = Disarm
            0, 0, 0, 0, 0, 0
        )

        # Step 3: Wait a bit to ensure the drone is armed
        asyncio.run(self.wait_for_arming(drone_id))

        # Step 4: Send TAKEOFF command
        print(f"Sending takeoff command to drone {drone_id} at {altitude}m altitude...")
        self.master.mav.command_long_send(
            drone_id,
            0,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0,
            0, 0, 0, 0,
            0, 0, altitude
        )
    
    def return_to_launch(self, drone_id):
        """Send the RTL command to the drone."""
        if not self.master:
            print(f"Cannot send RTL command: MAVLink is not connected!")
            return

        print(f"Sending RTL command to drone {drone_id}...")
        self.master.mav.command_long_send(
            drone_id,
            0,  # Target component
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH,
            0,  # Confirmation
            0,  # No parameters needed
            0, 0, 0, 0, 0, 0
        )
    
    def ack(self, keyword):
        """wait for the drone to acknowledge a command"""
        print(str(self.master.recv_match(type=keyword, blocking=True)))




if __name__ == "__main__":
    dispatcher = Dispatcher()
    dispatcher.recieve_packets()
