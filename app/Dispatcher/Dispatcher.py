
from pymavlink import mavutil
import asyncio

class Dispatcher:
    def __init__(self, missionState):
        self.master = None
        self.missionState = missionState
        
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
        """Continuously process all MAVLink packets without latency."""
        if not self.master:
            print("No MAVLink connection established.")
            return

        try:
            while True:
                # Process all available messages in one loop
                while True:
                    msg = self.master.recv_match(blocking=False)
                    if not msg:
                        break  # Exit when no more messages are in the buffer

                    drone_id = msg.get_srcSystem()
                    msg_type = msg.get_type()

                    if msg_type == "HEARTBEAT":
                        self.missionState.updateDroneStatus(drone_id, msg.system_status)
                        #print(f"Drone {drone_id} status: {msg.system_status}")

                    elif msg_type == "GLOBAL_POSITION_INT":
                        self.missionState.updateDronePosition(
                            drone_id, msg.lat, msg.lon, msg.alt, msg.relative_alt,
                            msg.hdg, msg.vx, msg.vy, msg.vz
                        )
                        #print(f"Drone {drone_id} position: {msg.lat}, {msg.lon}, {msg.alt}")

                    elif msg_type == "ATTITUDE":
                        self.missionState.updateDroneTelemetry(
                            drone_id, msg.roll, msg.pitch, msg.yaw
                        )
                        #print(f"Drone {drone_id} telemetry: {msg.roll}, {msg.pitch}, {msg.yaw}")
                    
                    elif msg_type == "MISSION_COUNT":
                        #self.missionState.updateDroneMissionCount(drone_id, msg.count)
                        print(f"Drone {drone_id} mission count: {msg.count}")

                await asyncio.sleep(0.005)


        except KeyboardInterrupt:
            print("\nStopping Dispatcher...")
        finally:
            self.master.close()

    def clear_mission(self, drone_id):
        self.master.target_system = drone_id
        self.master.waypoint_clear_all_send()


if __name__ == "__main__":
    dispatcher = Dispatcher()
    dispatcher.recieve_packets()
