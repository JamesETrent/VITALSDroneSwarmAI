# import socket

# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# host = '127.0.0.1'
# port = 14550
# s.connect((host,port))
# print("Connected to server")
# try:
#     while True:
#         data = s.recv(1024)  # Receive up to 1024 bytes at a time
#         if not data:
#             break  # Break if the connection is closed
#         print(f"Received Packet: {data.hex()}")  # Print in hex format
# except KeyboardInterrupt:
#     print("\nStopping...")
# finally:
#     s.close()

from pymavlink import mavutil

master = mavutil.mavlink_connection('tcp:127.0.0.1:14550')



while True:
    msg = master.recv_match(blocking=True)
    if msg:
        print(msg)
