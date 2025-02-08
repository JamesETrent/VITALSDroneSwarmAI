
from pymavlink import mavutil
import asyncio

class Dispatcher:
    def __init__(self, missionState):
        self.master = mavutil.mavlink_connection('tcp:127.0.0.1:14550', mavlink_version="2.0")
        self.missionState = missionState
        

    async def receive_packets(self):
        """Continuously process all MAVLink packets without latency."""
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
                        print(f"Drone {drone_id} status: {msg.system_status}")

                    elif msg_type == "GLOBAL_POSITION_INT":
                        self.missionState.updateDronePosition(
                            drone_id, msg.lat, msg.lon, msg.alt, msg.relative_alt,
                            msg.hdg, msg.vx, msg.vy, msg.vz
                        )
                        print(f"Drone {drone_id} position: {msg.lat}, {msg.lon}, {msg.alt}")

                    elif msg_type == "ATTITUDE":
                        self.missionState.updateDroneTelemetry(
                            drone_id, msg.roll, msg.pitch, msg.yaw
                        )
                        print(f"Drone {drone_id} telemetry: {msg.roll}, {msg.pitch}, {msg.yaw}")

                await asyncio.sleep(0.005)


        except KeyboardInterrupt:
            print("\nStopping Dispatcher...")
        finally:
            self.master.close()

if __name__ == "__main__":
    dispatcher = Dispatcher()
    dispatcher.recieve_packets()



# master = mavutil.mavlink_connection('tcp:127.0.0.1:14550')
# try:
#     while True:
#         msg = master.recv_match(blocking=True, type='HEARTBEAT')
        
#         if msg:
#             print(msg.get_srcSystem())
#             print(msg)
#         msg = master.recv_match(blocking=True, type='GLOBAL_POSITION_INT')
        
#         if msg:
#             print(msg.get_srcSystem())
#             print(msg)
#         msg = master.recv_match(blocking=True, type='ATTITUDE')
        
#         if msg:
#             print(msg.get_srcSystem())
#             print(msg)
# except KeyboardInterrupt:
#     print("\nStopping...")
# finally:
#     master.close()


