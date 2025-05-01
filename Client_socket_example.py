#!/usr/bin/python3

import socket

server_ip = '127.0.0.1'
port = 12345

s = socket.socket()
s.connect((server_ip, port))


s.sendall(b'Hello server')
data = s.recv(1024)
if data:
    print("Received from server:", data.decode())
wait = input("Press Enter to continue...")

print("\nClient stopped by user")
s.close()
print("Socket closed")
wait = input("Press Enter to continue...")



