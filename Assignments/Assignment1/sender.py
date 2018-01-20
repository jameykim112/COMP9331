import socket
import sys
import time
import struct
import pickle
import random

### FUNCTIONS ###
def read_data(file_name):
    with open(file_name, "r+") as f_o:
        data = f_o.read()#.replace('\n', '') #Read entire file at once, data from application layer
    return data
# Break down data into Maximum Segment Size packets
def data_segmenting(full_data, start_segment, MSS):
    MSS = int(MSS)
    end_segment = start_segment + MSS #Convert MSS to int as input as string
    data_segment = full_data[start_segment:(start_segment+MSS)] # Create data segment
    return data_segment, start_segment, end_segment

def sender_log(send_type, start_time, packet_type, packet):
    end = time.perf_counter()
    run_time = format((end - start)*1000, '.3f')
    with open('Sender_log.txt', 'a+') as sender_log:
        #sender_log.write(send_type + ' ' + str(run_time) + ' ' + packet_type + ' ' + str(packet[1]) + ' ' + str(len(packet[6])) + ' ' + str(packet[2]) + '\n')
        #sender_log.write(send_type + ' ' + str(run_time) + ' ' + packet_type + ' ' + str(packet[1]) + ' ' + str(len(packet[6])) + ' ' + str(packet[2]) + '\n')
        sender_log.write("{:<4}  {:<11}  {:<2}  {:>5}  {:>5}  {:>5}\n".format(send_type, run_time, packet_type, packet[1], len(packet[6]), packet[2]))
    return

def final_log(data_transferred, segments_sent, packets_dropped, segments_retransmitted, duplicate_ack):
    with open('Sender_log.txt', 'a+') as sender_log:
        sender_log.write('\n' +
                        'Amount of (original) Data Transferred: '+ str(data_transferred) + '\n' +
                        'Number of Data Segments Sent: '+ str(segments_sent) + '\n' +
                        'Number of (all) Packets Dropped: '+ str(packets_dropped) + '\n' +
                        'Number of Retransmitted Segments: '+ str(segments_retransmitted) + '\n'
                        'Number of Duplicate Acknowledgements received: '+ str(duplicate_ack) + '\n'
                        )


def three_way_handshake(sock, receiver_host_ip_port, receiver_port, start): #PAGE 252
    #ALSO INITIATE A TIMEOUT VALUE IN MILLISECONDS
    seq_num = 0 # Initially 0
    ack_num = 0 # Initially 0
    SYN = 1 # SYN always starts as 1
    ACK = 0
    FIN = 0
    totalfilesize = 0
    payload = ''
    packet_fmt = "iii???{}s"

    # Send SYN to server
    packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]
    packet[6] = bytes(packet[6], 'utf-8')
    packed_packet = struct.pack(packet_fmt.format(len(packet[6])), int(packet[0]), packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])
    sock.sendto(packed_packet,(receiver_host_ip, int(receiver_port)))
    sender_log('snd', start, 'S', packet)
    print('SYN sent to sender')

    # Receive SYNACK from server
    data, address = sock.recvfrom(buffer_size)
    payload_b = len(data) - struct.calcsize(packet_fmt[:6])
    receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload = struct.unpack(packet_fmt.format(payload_b),data)
    packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]
    sender_log('rcv', start, 'SA', packet)
    if packet[3] == 1 and packet[4] == 1: #If SYNACK received from Server
        print("SYNACK received from receiver")

        # Send ACK to receiver to complete 3-way handshake
        seq_num = packet[2]
        packet[3] = 0 #SYN bit set to 0
        packet[1] = seq_num

        print("Sending ACK to server, header values are")
        print(packet)
        packed_packet = struct.pack(packet_fmt.format(len(packet[6])), int(packet[0]), packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])
        sock.sendto(packed_packet,(receiver_host_ip, int(receiver_port)))
        sender_log('snd', start, 'A', packet)
        return True, packet
    else:
        return False

def PLD_module(pdrop):
    if pdrop >= 0 or pdrop <= 1:
        number = random.random()
        #print("Random number is: " + str(number))
        if number > pdrop:
            return False
        else:
            return True
    else:
        print('Incorrect pdrop value, please insert a value between 0 and 1')
        sys.exit()


### MAIN ###
global buffer_size
start_segment = 0
totalsentfile = 0
done = False
buffer_size = 4096

# RUN A CHECK TO CHECK ALL INPUT VALUES BEFORE RUNNING FULL PROGRAM
receiver_host_ip = sys.argv[1]
receiver_port = sys.argv[2]
file_name = sys.argv[3]
MWS = int(sys.argv[4]) #Maximum Window Size
MSS = int(sys.argv[5]) #Maximum Segment Size
timeout = int(sys.argv[6])/1000 #Value of timeout in milliseconds
pdrop = float(sys.argv[7])
seed = int(sys.argv[8])
random.seed(seed)
window = []
window_capacity = 0
rcv_packet = []
ack_d = {}
duplicate_ack = 0

start = time.perf_counter()
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('',0))


open('Sender_log.txt', 'w+')
try:
    connection_established, packet = three_way_handshake(sock, receiver_host_ip, receiver_port, start)
    packet[4] = 0
    packet[5] = 0
    iteration = 0
    done = False
    mw_packets = round(MWS/MSS)
    acktotal = 0
    payload_final = 0

    #Variables for log file
    data_transferred = 0
    segments_sent = 0
    packets_dropped = 0
    segments_retransmitted = 0


    if connection_established == True:
        print("*** 3 WAY HANDSHAKE SUCCESFUL ***")
        print("MWS is:", MWS)
        content = read_data(file_name) #Read content from file
        #packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]
        base = 1 #Starts at 1
        nextSeqnum = 1
        lastackreceived = time.time()
        sock.setblocking(False)

        while acktotal < len(content):
        #while ((totalsentfile < len(content))) or not done or window:
            #Checking whether window is full
            if (window_capacity <= MWS) and len(window) < mw_packets and not done:# or not done:
                #Create payload
                #If at end of file and remaining bytes < MSS
                if totalsentfile + MSS > len(content):
                    #Create a buffer to ensure acknowledged on receiver
                    buffer_string = MSS - len(content[totalsentfile:])
                    payload = content[totalsentfile:] + ' ' * buffer_string
                    payload_final = len(content[totalsentfile:])
                    #print(totalsentfile, MSS)
                    #print("At end of file")
                    #if not window:
                        #None
                        #packet[5] = 1
                    done = True
                    totalsentfile += MSS
                    data_transferred += payload_final
                    segments_sent += 1
                    #If remaining bytes > len(content)
                else:
                    payload = content[totalsentfile:totalsentfile + MSS]
                    totalsentfile += MSS
                    data_transferred += len(payload)
                    segments_sent += 1

                if (window_capacity + len(payload) <= MWS):
                    #Pack and send packet
                    #Pack
                    packet_fmt = "iii???{}s"
                    payload_b = bytes(payload, 'utf-8')
                    packet[6] = payload_b
                    packet[0] = int(packet[0]) #Converion of element 0 to integer
                    packet[2] = packet[1] #Update ACK number
                    #Increment seq number
                    if iteration == 0:
                        packet[1] = 1
                        iteration += 1
                    elif iteration > 0:
                        packet[1] = packet[1] + len(payload)
                        iteration += 1
                    packed_packet = struct.pack(packet_fmt.format(len(payload_b)), packet[0], packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])

                    #Increase window capacity and append window packet
                    print("Increasing window capacity and appending window packet")
                    window_capacity += len(payload)
                    window.append([packet[0], packet[1], packet[2], packet[3], packet[4], packet[5], packet[6]])
                    print(window)

                    #Packet dropped or transmitted
                    dropped = PLD_module(pdrop)
                    if dropped == False:
                        #Send to sender
                        sock.sendto(packed_packet,(receiver_host_ip, int(receiver_port)))
                        sender_log('snd', start, 'D', packet)
                        print("Sent packet seq: " + str(packet[1]))
                        print(packet)
                        #print("Sent packet window is: ")
                        #print(window)
                        sock.settimeout(timeout)
                    elif dropped == True:
                        packets_dropped += 1
                        print("Dropped")
                        sender_log('drop', start, 'D', packet) #Dropped packet
                        time.sleep(timeout) #Artificial delay of timer
                        pass

            #RECEIVE ACK
            else:
                try:
                    print("Receiving packet")
                    data, address = sock.recvfrom(4096)
                    receiver_port, seq_num, ack_num, SYN, ACK, FIN = struct.unpack(packet_fmt[:6].format(payload_b),data)
                    rcv_packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, '']
                    sender_log('rcv', start, 'D', rcv_packet)
                    print("Received packet")
                    print(rcv_packet)
                    #sender_log('rcv', start, 'A', packet)
                    #While received seq number > window seq number
                    #print("Window is: ")
                    print(window)
                    #Most recent ack
                    try:
                        while rcv_packet[2] > window[0][1]:
                            lastackreceived = time.time()
                            window_capacity -= len(window[0][6])
                            if window[0][1] in ack_d:
                                duplicate_ack += 1
                            else:
                                ack_d[window[0][1]] = window[0]

                            print("Acknowledged sequence", window[0][1])
                            acktotal = window[0][1] + payload_final
                            print(acktotal)
                            del window[0]
                            if not window and totalsentfile >= len(content):
                                done = True
                    except IndexError:
                        pass
                except:
                    print("Timed out")
                    print(window_capacity)
                    print(totalsentfile)
                    print(len(content))
                    print(window)
                    done
                    if (time.time() - lastackreceived) > timeout:
                        for packet in window:
                            print("Re-transmitting", packet)
                            packed_packet = struct.pack(packet_fmt.format(len(payload_b)), packet[0], packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])
                            sock.sendto(packed_packet,(receiver_host_ip, int(receiver_port)))
                            sender_log('snd', start, 'D', packet)
                            segments_retransmitted += 1
                    elif not window and (totalsentfile >= len(content)):
                        done = True
                        #packet[5] = 1
                    else:
                        pass
        ### Four-segment connection termination ###
        print("***Starting four way termination")
        FIN = False
        FINACK = False
        ACK = False
        termination = True


        while termination == True:
            if FIN == False:
                packet[6] = bytes('', 'utf-8')
                packet[5] = 1
                packed_packet = struct.pack(packet_fmt.format(len(packet[6])), int(packet[0]), packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])
                sock.sendto(packed_packet,(receiver_host_ip, int(receiver_port)))
                sender_log('snd', start, 'F', packet)
                FIN = True

            elif FINACK == False:
                data, address = sock.recvfrom(buffer_size) #Wait for data to be sent from sender
                payload_b = len(data) - struct.calcsize(packet_fmt[:6])
                receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload = struct.unpack(packet_fmt.format(len(packet[6])),data)
                packet = [receiver_port, seq_num, ack_num, SYN, ACK, FIN, payload]
                sender_log('rcv', start, 'FA', packet)
                FINACK = True

            elif ACK == False:
                packed_packet = struct.pack(packet_fmt.format(len(packet[6])), int(packet[0]), packet[1], packet[2], packet[3], packet[4], packet[5], packet[6])
                sock.sendto(packed_packet,(receiver_host_ip, int(receiver_port)))
                packet[1] = packet[2]
                sender_log('snd', start, 'A', packet)
                termination = False
                ACK = True

        final_log(data_transferred, segments_sent, packets_dropped, segments_retransmitted, duplicate_ack)

        print("File transfer complete")
        sys.exit()
    else:
        print("Error 3-way handshake failed")
except FileNotFoundError:
    print("Error file not found")
    sys.exit()
