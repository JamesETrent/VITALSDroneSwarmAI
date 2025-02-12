
from pymavlink import mavutil

class Dispatcher:
    def __init__(self):
        self.master = mavutil.mavlink_connection('tcp:127.0.0.1:14550', mavlink_version="2.0")
        

    def recieve_packets(self):
        try:
            while True:
                msg = self.master.recv_match(blocking=True, type='HEARTBEAT')
                
                if msg:
                    print(msg.get_srcSystem())
                    print(msg)
                msg = self.master.recv_match(blocking=True, type='GLOBAL_POSITION_INT')
                
                if msg:
                    print(msg.get_srcSystem())
                    print(msg)
                msg = self.master.recv_match(blocking=True, type='ATTITUDE')
                
                if msg:
                    print(msg.get_srcSystem())
                    print(msg)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self.master.close()

if __name__ == "__main__":
    dispatcher = Dispatcher()
    dispatcher.recieve_packets()






