## COMP9331 - Assignment 1
## Receiver codebase
## By Jamey Kim - z3251762
### PYTHON 3 USED ###

import socket
import sys
import time
import pickle
import struct
import os

## Command line arguments
receiver_port = sys.argv[1]
file_name = sys.argv[2]
connection_established = False
FIN = 0
expecting_seq = 1
buffer_size = 4096
iteration = 0

#Variables for log file
data_received = 0
segments_received = 0
duplicates_received = 0
segment_d = {}

def receiver_log(send_type, start_time, packet_type, packet):
    end = time.perf_counter()
    run_time = format((end - start)*1000, '.3f')
    with open('Receiver_log.txt', 'a+') as receiver_log:
        #receiver_log.write(send_type + ' ' + str(run_time) + ' ' + packet_type + ' ' + str(packet[1]) + ' ' + str(len(packet[6])) + ' ' + str(packet[2]) + '\n')
        receiver_log.write("{:<4}  {:<11}  {:<2}  {:>5}  {:>5}  {:>5}\n".format(send_type, run_time, packet_type, packet[1], len(packet[6]), packet[2]))
    return

def final_log(data_received, segments_received, duplicates_received):
    with open('Receiver_log.txt', 'a+') as receiver_log:
        receiver_log.write('\n' +
                        'Amount of (original) Data Received: '+ str(data_received) + '\n' +
                        'Number of Data Segments Received: '+ str(segments_received) + '\n' +
                        'Number of duplicate segments received: '+ str(duplicates_received) + '\n')


try:
    send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    recv_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    recv_sock.bind(('', int(receiver_port)))
except OSError:
    print("Error port " + receiver_port + " in use, select different Port")
    sys.exit()

#Overwrite any existing files
open(file_name, 'w+')
open('Receiver_log.txt', 'w+')
while True:

    #Three-way handshake
    if connection_established == False:
        try:
            packet_fmt = "iii???{}s"
            #Receive SYN from sender
            data, address = recv_sock.recvfrom(4096) #receive data
            start = time.perf_counter()
            payload_b = len(data) - struct.calcsize(packet_fmt[:6])
            receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload = struct.unpack(packet_fmt.format(payload_b),data)
            packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]
            receiver_log('rcv', start, 'S', packet)
            if packet[3] == 1 and packet[4] == 0:
                print("SYN received from sender")
                print("Address is " + str(address))

                #Send SYNACK to sender
                packet[2] = packet[1] + 1
                packet[4] = 1 #Set ACK to 1
                print("Sending SYN+ACK to client, header values are")
                print(packet)
                packed_packet = struct.pack(packet_fmt.format(len(packet[6])), packet[0], packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])
                send_sock.sendto(packed_packet, address) # Send to client
                receiver_log('snd', start, 'SA', packet)
                # Receive ACK from Client
                data, address = recv_sock.recvfrom(4096) #receive data
                receiver_log('rcv', start, 'A', packet)
                payload_b = len(data) - struct.calcsize(packet_fmt[:6])
                receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload = struct.unpack(packet_fmt.format(payload_b),data)
                packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]
                print("Address is " + str(address))
                if packet[3] == 0 and packet[4] == 1:
                    print("ACK received from sender")
                    print("*** 3 WAY HANDSHAKE SUCCESFUL ***")
                    connection_established = True
        except OSError:
            print("Port " + receiver_port + " in use")
            sys.exit()

    #Payload data being received from sender

    elif connection_established == True or packet[5] == 0:
        print('Payload data being received from sender')
        # #Receive from sender
        packet_fmt = "iii???{}s"
        data, address = recv_sock.recvfrom(buffer_size) #Wait for data to be sent from sender
        payload_b = len(data) - struct.calcsize(packet_fmt[:6])
        receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload = struct.unpack(packet_fmt.format(payload_b),data)
        packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]

        print("Packet received")
        print(packet)
        if packet[5] != 1: #If not FIN = 1
            receiver_log('rcv', start, 'D', packet)
            #Check whether packet received is a duplicate
            if packet[1] in segment_d:
                print("Duplicate is: ", packet)
                duplicates_received += 1
            else:
                segment_d[packet[1]] = packet

            # Check whether correct SEQ has been received
            print("seq_num: " + str(packet[1]))
            print("expecting_sequence: " + str(expecting_seq))
            if packet[1] == expecting_seq:
                print("Received in order")
                with open(file_name, 'a+') as receiver_file:
                    receiver_file.write(payload.decode('utf-8'))
                    data_received += len(payload)
                    segments_received += 1
                    #Acknowledge received payload
                ack_num = seq_num + int(len(packet[6]))
                expecting_seq = ack_num
                most_recently_ack_packet = packet

                packed_packet = struct.pack(packet_fmt[:6], receiver_port, seq_num, ack_num, SYN, ACK, FIN)
                send_sock.sendto(packed_packet, address)

                print("Packet sent to sender")
                packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, '']
                receiver_log('snd', start, 'D', packet)
                print(packet)
            #print(payload.decode('utf-8'))
            #discard packet and resend ACK for most recently received inorder pkt
            elif iteration > 0:
                print("Received out of order")
                print("Resending ACK for most recently received inorder packet")
                print(most_recently_ack_packet)
                packed_packet = struct.pack(packet_fmt[:6], most_recently_ack_packet[0], most_recently_ack_packet[1], most_recently_ack_packet[2], most_recently_ack_packet[3], most_recently_ack_packet[4], most_recently_ack_packet[5])
                send_sock.sendto(packed_packet, address)
                receiver_log('snd', start, 'A', packet)
            else:
                pass


    #Four way termination
        elif packet[5] == 1:

            with open(file_name, 'r+') as receiver_file:
                lines = receiver_file.readlines()
                data_received -= len(lines[-1])
                lines[-1].strip()
            

            with open(file_name, 'w+') as final_file:
                for i in range(0, len(lines) - 1):
                    final_file.write(lines[i])

            termination = True
            FINACK = False
            ACK = False
            while termination == True:
                if FINACK == False:
                    print("STARTING FOUR WAY TERMINATION")
                    #PACKET ALREADY RECEIVED UP TOP AT START WHILE loop
                    receiver_log('rcv', start, 'F', packet)
                    packed_packet = struct.pack(packet_fmt.format(len(packet[6])), int(packet[0]), packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])
                    send_sock.sendto(packed_packet, address)
                    packet[2] = packet[1] + 1
                    receiver_log('snd', start, 'FA', packet)
                    FINACK = True
                elif ACK == False:
                    data, address = recv_sock.recvfrom(buffer_size) #Wait for data to be sent from sender
                    receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload = struct.unpack(packet_fmt.format(len(packet[6])),data)
                    packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]
                    receiver_log('rcv', start, 'A', packet)
                    ACK = True
                else:
                    final_log(data_received, segments_received, duplicates_received)
                    termination = True
                    print("File Transfer Complete")
                    sys.exit()
