## COMP9331 - Assignment 1
## Sender codebase
## By Jamey Kim - z3251762
### PYTHON 3 USED ###

import socket
import sys
import time

## Command line arguments
receiver_host_ip = sys.argv[1]
receiver_port = sys.argv[2]
file_name = sys.argv[3]
# MWS = sys.argv[4] #Maximum Window Size
# MSS = sys.argv[5] #Maximum Segment Size
# timeout = sys.argv[6]
# pdrop = sys.argv[7]
# seed = sys.argv[8]


## Define data structure for 3-way handshake SYN, SYN+ACK, ACK
#data_packet = [seq, ack, data]
with open(file_name, "r+") as f_o:
    data = f_o.read().replace('\n', '') #Read entire file at once
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


data_bytes = str.encode(data) ## Encode data into binary utf-8 for sending
send_packet = sock.sendto(data_bytes,(receiver_host_ip, int(receiver_port)))
sock.close()

# for i in range(0,10):
#     #Create Ping payload to be sent to server
#     start = time.perf_counter()
#     send_message = 'Ping to ' + str(UDP_IP_SERVER) + ' seq = ' + str(i) + str(start) + 'ms'
#     send_message_bytes = str.encode(send_message)
#     sent = sock.sendto(send_message_bytes,(UDP_IP_SERVER, int(UDP_PORT_SERVER)))
#
#     #Wait upto 1 second for reply, if reply print, else continue next loop
#     try:
#         data, address = sock.recvfrom(110)
#     except socket.timeout:
#         print('Ping to ' + str(UDP_IP_SERVER) + ' seq = ' + str(i) + ' has timed out')
#         continue
#     if data != '':
#         end = time.perf_counter()
#         rtt = format((end - start)*1000, '.3f')
#         print('Ping to ' + str(UDP_IP_SERVER) + ' seq = ' + str(i) + ' RTT = ' + str(rtt) + 'ms')
#
# sock.close()
