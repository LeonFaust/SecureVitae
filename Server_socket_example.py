#!/usr/bin/python3

import socket

s = socket.socket()
port = 12345
s.bind(('127.0.0.1', port))
print(f"Socket binded to {port}")

s.listen(5)
print("Socket is listening — Press Ctrl+C to quit")

try:
    while True:
        c, addr = s.accept()
        print('Got connection from', addr)

        data = c.recv(2048)  # Aumentei o buffer para garantir mais espaço
        if data:
            message = data.decode()
            print("Received from client:", message)

            # Guardar no ficheiro (acrescentar no final)
            with open("received_data.txt", "a") as f:
                f.write(f"From {addr}:\n{message}\n{'-'*40}\n")

            c.send('Thank you for connecting'.encode())

        c.close()

except KeyboardInterrupt:
    print("\nServer stopped by user")

finally:
    s.close()
    print("Socket closed")
