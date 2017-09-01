## COMP9331 - Assignment 1
## Receiver codebase
## By Jamey Kim - z3251762
### PYTHON 3 USED ###

import socket
import sys
import time

## Command line arguments
receiver_port = sys.argv[1]
file_name = sys.argv[2]
f_o = open(file_name, "w")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('', int(receiver_port)))

while True:
    data, address = sock.recvfrom(1024) #receive data
    data = bytes.decode(data) # Decode from binary UTF-8 -> string
    with open(file_name, "w+") as f_o: # Create new file called file_name in directory and overwrites
        # Include a loop to write to file
        f_o.write(data)
