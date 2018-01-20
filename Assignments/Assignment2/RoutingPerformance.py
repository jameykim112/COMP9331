import sys, time, math, argparse, random
##import numpy as np

AVAILABLE = 1
BUSY = 0

class Graph(object):

    def __init__(self, nV=None, nE=None):
        self.nV = nV
        self.nE = nE
        self.edges         = [[(0,-1,-1)]*self.nV for i in range(self.nV)]
        self.link_capacity = [[0]*self.nV for i in range(self.nV)]
        self.link_status   = [[0]*self.nV for i in range(self.nV)]
        for i in range(self.nV):
            self.edges[i][i]         = (1,0,0)
            self.link_capacity[i][i] = 1
            self.link_status[i][i]   = 1

    def validVertex(self, vertex):
        if vertex >= 0 and vertex < self.nV:
            return True
        else:
            return False

    def insertEdge(self, vertex_1, vertex_2, edge_info):
        if self.validVertex(vertex_1) and self.validVertex(vertex_2):
            self.edges[vertex_1][vertex_2] = edge_info
            self.edges[vertex_2][vertex_1] = edge_info
        else:
            pass

    # Link info is the maximum avaiable connections a link (edge from vertex_1 to vertext_2) can handle.
    # This is constant and will not change during the entire transmission.
    def insertLinkCapacity(self, vertex_1, vertex_2, link_info):
        if self.validVertex(vertex_1) and self.validVertex(vertex_2):
            self.link_capacity[vertex_1][vertex_2] = link_info
            self.link_capacity[vertex_2][vertex_1] = link_info
        else:
            pass
    # Link status indicates whether a link (edge from vertex_1 to vertex_2) is BUSY or AVAILABLE
    def modifyLinkStatus(self, vertex_1, vertex_2, new_status):
        if self.validVertex(vertex_1) and self.validVertex(vertex_2):
            self.link_status[vertex_1][vertex_2] = new_status
            self.link_status[vertex_2][vertex_1] = new_status
        else:
            pass

    def removeEdge(self, vertex_1, vertex_2, edge_info):
        if self.validVertex(vertex_1) and self.validVertex(vertex_2):
            if not self.edges[vertex_1][vertex_2] == (0,-1,-1):
                self.edges[vertex_1][vertex_2] = (0,-1,-1)
                self.edges[vertex_2][vertex_1] = (0,-1,-1)
        else:
            pass

    def adjacent(self, vertex_1, vertex_2):
        if self.validVertex(vertex_1) and self.validVertex(vertex_2):
            if not self.edges[vertex_1][vertex_2] == (0,-1,-1):
                return True
            else:
                return False

    def showGraph(self):
        for row in self.edges:
            for val in row:
                print(val,end = ' ')
            print()

def routing_SHP(graph, source, destination):
    global list_of_nodes
    dist = [math.inf] * graph.nV
    dist[source] = 0
    pred = [[] for i in range(graph.nV)]
    vDict = dict()
    for vertex in range(graph.nV):
        vDict[vertex] = dist[vertex]

    while len(vDict) != 0:
        min_node = sorted(vDict,key=vDict.get)[0]
        if min_node == destination:
            break
        for node in [x for x in range(graph.nV)]:
            if graph.adjacent(min_node, node):
                if node == min_node:
                    weight = 0
                else:
                    weight = graph.edges[min_node][node][0]
                    if dist[min_node]+weight <= dist[node]:
                        dist[node] = dist[min_node] + weight
                        vDict[node] = dist[node]
                        pred[node].append(min_node)
        del vDict[min_node]
    current_node = destination
    path = list()
    path.append(destination)

    while current_node != source:
        selected_node = random.choice(pred[current_node])
        path.append(selected_node)
        current_node = selected_node
    path = path[::-1]
    return path

def routing_SDP(graph, source, destination):
    global list_of_nodes
    dist = [math.inf] * graph.nV
    dist[source] = 0
    pred = [[] for i in range(graph.nV)]
    vDict = dict()
    for vertex in range(graph.nV):
        vDict[vertex] = dist[vertex]

    while len(vDict) != 0:
        min_node = sorted(vDict,key=vDict.get)[0]
        if min_node == destination:
            break
        for node in [x for x in range(graph.nV)]:
            if graph.adjacent(min_node, node):
                if node == min_node:
                    weight = 0
                else:
                    weight = graph.edges[min_node][node][1]
                    if dist[min_node]+weight <= dist[node]:
                        dist[node] = dist[min_node] + weight
                        vDict[node] = dist[node]
                        pred[node].append(min_node)
        del vDict[min_node]
    current_node = destination
    path = list()
    path.append(destination)

    while current_node != source:
        selected_node = random.choice(pred[current_node])
        path.append(selected_node)
        current_node = selected_node
    path = path[::-1]
    return path

def routing_LLP(graph, source, destination):
    global list_of_nodes
    # Find all possible paths using DFS.
    paths = find_all_paths_DFS(graph, source, destination)

    loads_on_paths = list()
    for i,path in enumerate(paths):
        # For each path in paths, find all the loads of all the links on the current path.
        loads_on_current_path = [(graph.link_capacity[path[k]][path[k+1]]-graph.edges[path[k]][path[k+1]][2])/graph.link_capacity[path[k]][path[k+1]] for k in range(len(path)-1)]
        # Return the maximum load on the current path as the load for that path.
        load_of_current_path = max(loads_on_current_path)
        loads_on_paths.append(load_of_current_path)

    # From all the possible paths, find the minimum load.
    searchVal = min(loads_on_paths)
    # Find all the paths that have the minimum load.
    possible_paths = [i for i, x in enumerate(loads_on_paths) if x == searchVal]
    # Choose randomly a path from the list of all possible paths.
    least_loaded_path = random.choice(possible_paths)
    return paths[least_loaded_path], paths

# DFS to find all possible paths from SOURCE to DESTINATION
def find_all_paths_DFS(graph, start, end, path=[]):
    path = path + [start]
    if start == end:
        return [path]
    paths = []
    for node in range(graph.nV):
        if graph.adjacent(start, node):
            if node not in path:
                newpaths = find_all_paths_DFS(graph, node, end, path)
                for newpath in newpaths:
                    paths.append(newpath)
    return paths

def updateCapacity(graph, time, data_rate, routing_protocol, statistics):
    global list_of_nodes
    global routed_request
    global total_request
    global successful_packets
    global workload_d
    global path_d
    source = workload_d[time][1]
    destination = workload_d[time][2]

    #If transmission being opened from source to destination
    if workload_d[time][0] == 0:
        ##total_request += 1
        if (routing_protocol == 'SHP'):
            path = routing_SHP(graph, source, destination)
        elif (routing_protocol == 'SDP'):
            path = routing_SDP(graph, source, destination)
        elif (routing_protocol == 'LLP'):
            path, paths = routing_LLP(graph, source, destination)

        can_be_routed = 1
        for i in range(len(path)-1):
            # Check the current status of the requested link. If AVAILABLE, proceed, if not, discard.
            if (graph.edges[path[i]][path[i+1]][2] == 0):
                connection_status[time] = 0 # None packets of the requested connection can be sent.
                workload_d[workload_d[time][3]][0] = -1 # Connection has been discarded. The end time for this connection is no longer valid.
                can_be_routed = 0
                break

        if can_be_routed == 1:
            path_d[workload_d[time][3]] = path #Store path Key = Connection end time, Value = Path array
            routed_request += 1
            successful_packets += workload_d[time][4]
            statistics[time][0] = (len(path)-1) # Nb of hops required to go from source to destination
            for i in range(len(path)-1):
                update_capacity = graph.edges[path[i]][path[i+1]][2] - 1
                statistics[time][1] = statistics[time][1] + graph.edges[path[i]][path[i+1]][1] # Cumulative prop. delay from source to destination
                connection_status[time] = 1

                graph.edges[path[i]][path[i+1]] = (graph.edges[path[i]][path[i+1]][0], graph.edges[path[i]][path[i+1]][1], update_capacity)
                graph.edges[path[i+1]][path[i]] = (graph.edges[path[i+1]][path[i]][0], graph.edges[path[i+1]][path[i]][1], update_capacity)

                if update_capacity == 0:
                    graph.modifyLinkStatus(path[i], path[i+1], BUSY)
                    graph.modifyLinkStatus(path[i+1], path[i], BUSY)

    #If transmission is being closed from source to destination
    elif workload_d[time][0] == 1:
        if time in path_d:
            path = path_d[time] #Path is extracted from dictionary based on the end time
            for i in range(len(path)-1):
                update_capacity = graph.edges[path[i]][path[i+1]][2] + 1
                graph.edges[path[i]][path[i+1]] = (graph.edges[path[i]][path[i+1]][0], graph.edges[path[i]][path[i+1]][1], update_capacity)
                graph.edges[path[i+1]][path[i]] = (graph.edges[path[i+1]][path[i]][0], graph.edges[path[i+1]][path[i]][1], update_capacity)
                if update_capacity >= 0:
                    graph.modifyLinkStatus(path[i], path[i+1], AVAILABLE)
                    graph.modifyLinkStatus(path[i+1], path[i], AVAILABLE)
        else:
            return
    else:
        pass

### Read command line inputs ###
parser = argparse.ArgumentParser()
parser.add_argument("network_scheme", help="Input network type") #Read in as string
parser.add_argument("routing_scheme", help="Input routing scheme SHP, SDP or LLP") #Read in as string
parser.add_argument("topology_file", help="Input name of topology file")
parser.add_argument("workload_file", help="Input name of workload file")
parser.add_argument("packet_rate", help="Positive integer showing number of packet per second", type = int)
args = parser.parse_args()

network_scheme = args.network_scheme
routing_scheme = args.routing_scheme
topology_file = args.topology_file
workload_file = args.workload_file
packet_rate = args.packet_rate

#topology_file = "topology_sample.txt"
lines = [line.rstrip('\n') for line in open(topology_file)]

list_of_nodes = []
for line in lines:
    line_content = line.split()
    if line_content[0] not in list_of_nodes:
        list_of_nodes.append(line_content[0])
    if line_content[1] not in list_of_nodes:
        list_of_nodes.append(line_content[1])

list_of_nodes = sorted(list_of_nodes)

total_nb_of_nodes = len(list_of_nodes)

graph = Graph(total_nb_of_nodes)

for line in lines:
    line_content = line.split()
    entry = (1,int(line_content[2]), int(line_content[3]))
    graph.insertEdge(list_of_nodes.index(line_content[0]), list_of_nodes.index(line_content[1]), entry)
    graph.insertLinkCapacity(list_of_nodes.index(line_content[0]), list_of_nodes.index(line_content[1]), entry[2])
    graph.modifyLinkStatus(list_of_nodes.index(line_content[0]), list_of_nodes.index(line_content[1]), AVAILABLE)

#workload_file = "workload_sample.txt"
lines = [line.rstrip('\n') for line in open(workload_file)]

## Jamey: Retreive timestamps and control link capacity
times = []
end_value = []
workload_d = {} # Key = time, value = (start/end, src, dest)
path_d = {}

#packet_rate = 2
packet_interval = 1 / packet_rate ## Intervals at which packet sent
i = 0

statistics = dict() # For each connection (key), store nb_of_hops used and the cumulative propagation delay (value)
connection_status = dict() # For each connection (key), store total nb_of_packets to-be-sent and how many have been sent (value)
total_nb_of_packets = 0
successful_packets = 0
total_request = 0
#network_scheme = 'PACKET'

for line in lines:
    total_request += 1
    start, source, destination, duration = line.split()

    start = float(start)
    duration = float(duration)
    source = ord(source) - 65
    destination = ord(destination) - 65

    if network_scheme == 'CIRCUIT':
        times.append(float(start))

        end = float(format(float(start) + float(duration) + random.uniform(0.000001, 0.000005), '.10f'))

        #end = float(format((float(start) + float(duration)), '.6f'))
        times.append(end)

        nb_of_packets_for_this_request = math.floor(packet_rate*float(duration))
        workload_d[float(start)] = [0, source, destination, end, nb_of_packets_for_this_request]
        workload_d[end] = [1, source, destination]

        total_nb_of_packets += nb_of_packets_for_this_request
        statistics[float(start)] = [0,0]
        connection_status[float(start)] = 0
    elif network_scheme == 'PACKET':
        intervals = round(packet_rate * duration)
        for i in range(intervals):

            #Artificially decrease end time by 0.0001 so end time does not over write start time in workload_d
            #Ensure all start values are unique by checking whether key exists in dictionary

            start = float(format(start, '.10f'))

            end = float(format(start + packet_interval + random.uniform(0.00001,0.0000), '.10f'))

            # [1 = start time/0 = end time, source, destination, end time]
            nb_of_packets_for_this_request = math.floor(packet_rate*float(duration))
            workload_d[float(start)] = [0, source, destination, end, nb_of_packets_for_this_request]
            workload_d[end] = [1, source, destination]

            total_nb_of_packets += nb_of_packets_for_this_request
            statistics[float(start)] = [0,0]
            connection_status[float(start)] = 0

            # Append to timestamp array
            times.append(start)
            times.append(end)

            # Increment start time by packet_interval
            start += packet_interval

times = sorted(times)

routed_request = 0
#total_request = 0
for time in times:
    updateCapacity(graph, time, packet_rate, routing_scheme, statistics)

total_nb_of_hops_used = sum([x[0] for x in list(statistics.values())])
total_cumulative_propagation_delay = sum([x[1] for x in list(statistics.values())])
total_nb_of_blocked_packets = total_nb_of_packets - successful_packets

print('total number of virtual circuit requests:', total_request)
##print('number of successfully routed request:', routed_request)
print('total number of packets:', total_nb_of_packets)
print('number of successfully routed packets:', successful_packets),
print('percentage of successfully routed packets:', round((successful_packets/total_nb_of_packets)*100,2))
print('number of blocked packets:', total_nb_of_blocked_packets)
print('percentage of blocked packets:', round((total_nb_of_blocked_packets/total_nb_of_packets)*100,2))
print('average number of hops per circuit:', round(total_nb_of_hops_used/routed_request,2))
print('average cumulative propagation delay per circuit:', round(total_cumulative_propagation_delay/routed_request,2))
