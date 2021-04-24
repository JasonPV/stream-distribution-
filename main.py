import math
import time
import heapq
import numpy as np
from scipy.optimize import fsolve
from scipy import optimize
from parsing_networks import rewrite_network, rewrite_demand

while True:
    file1 = input('Input filename of network\n')
    try:
        rewrite_network(file1)
        break
    except FileNotFoundError:
        print('Input again')
        continue

while True:
    file2 = input('Input filename of demand\n')
    try:
        rewrite_demand(file2)
        break
    except FileNotFoundError:
        continue


class Zone:
    def __init__(self, _buf):
        self.zoneId = _buf[0]
        self.destList = []


class Node:
    def __init__(self, _buf):
        self.Id = _buf[0]
        self.outLinks = []
        self.inLinks = []
        self.label = float("inf")
        self.pred = ""


class Link:
    def __init__(self, _buf):
        self.tailNode = _buf[0]
        self.headNode = _buf[1]
        self.capacity = float(_buf[2]) # veh per hour
        self.length = float(_buf[3]) # Length
        self.fft = float(_buf[4]) # Free flow travel time (min)
        self.beta = float(_buf[6])
        self.alpha = float(_buf[5])
        self.speedLimit = float(_buf[7])
        #self.toll = float(_buf[9])
        #self.linkType = float(_buf[10])
        self.flow = 0.0
        self.cost =  float(_buf[4]) #float(_buf[4])*(1 + float(_buf[5])*math.pow((float(_buf[7])/float(_buf[2])), float(_buf[6])))


class Demand:
    def __init__(self, _buf):
        self.fromZone = _buf[0]
        self.toNode = _buf[1]
        self.demand = float(_buf[2])

def readDemand():
    inFile = open("demand.dat")
    line = inFile.readline().strip().split("\t")
    for x in inFile:
        line = x.strip().split("\t")
        tripSet[line[0], line[1]] = Demand(line)
        if line[0] not in zoneSet:
            zoneSet[line[0]] = Zone([line[0]])
        if line[1] not in zoneSet:
            zoneSet[line[1]] = Zone([line[1]])
        if line[1] not in zoneSet[line[0]].destList:
            zoneSet[line[0]].destList.append(line[1])

    inFile.close()
    print(len(tripSet), "OD pairs")
    print(len(zoneSet), "zones")

def readNetwork():
    inFile = open('network.dat')
    line = inFile.readline().strip().split("\t")
    for line in inFile:
        line = line.strip().split("\t")
        linkSet[line[0], line[1]] = Link(line)
        if line[0] not in nodeSet:
            nodeSet[line[0]] = Node(line[0])
        if line[1] not in nodeSet:
            nodeSet[line[1]] = Node(line[1])
        if line[1] not in nodeSet[line[0]].outLinks:
            nodeSet[line[0]].outLinks.append(line[1])
        if line[0] not in nodeSet[line[1]].inLinks:
            nodeSet[line[1]].inLinks.append(line[0])

    inFile.close()
    print(len(nodeSet), "nodes")
    print(len(linkSet), "links")


###########################################################################################################################

readStart = time.time()

tripSet = {}
zoneSet = {}
linkSet = {}
nodeSet ={}



readDemand()
readNetwork()

originZones = set([k[0] for k in tripSet])
print("Reading the network data took", round(time.time() - readStart, 2), "secs")

#############################################################################################################################
#############################################################################################################################


def DijkstraHeap(origin):
    for n in nodeSet:
        nodeSet[n].label = float("inf")
        nodeSet[n].pred = ""
    nodeSet[origin].label = 0.0
    nodeSet[origin].pred = "NA"
    SE = [(0, origin)]
    while SE:
        currentNode = heapq.heappop(SE)[1]
        currentLabel = nodeSet[currentNode].label
        for toNode in nodeSet[currentNode].outLinks:
            link = (currentNode, toNode)
            newNode = toNode
            newPred =  currentNode
            existingLabel = nodeSet[newNode].label
            newLabel = currentLabel + linkSet[link].cost
            if newLabel < existingLabel:
                heapq.heappush(SE, (newLabel, newNode))
                nodeSet[newNode].label = newLabel
                nodeSet[newNode].pred = newPred

def updateTravelTime():
    for l in linkSet:
        linkSet[l].cost = linkSet[l].fft*(1 + linkSet[l].alpha*math.pow((linkSet[l].flow*1.0/linkSet[l].capacity), linkSet[l].beta))


def findAlpha(x_bar):
    def df(alpha):
        sum_derivative = 0 ## this line is the derivative of the objective function.
        for l in linkSet:
            tmpFlow = (linkSet[l].flow + alpha*(x_bar[l] - linkSet[l].flow))
            tmpCost = linkSet[l].fft*(1 + linkSet[l].alpha*math.pow((tmpFlow*1.0/linkSet[l].capacity), linkSet[l].beta))
            sum_derivative = sum_derivative + (x_bar[l] - linkSet[l].flow)*tmpCost
        return sum_derivative
    sol2 = fsolve(df, np.array([0.1]))
    return max(0.1, min(1, sol2[0]))



def tracePreds(dest):
    prevNode = nodeSet[dest].pred
    spLinks = []
    while nodeSet[dest].pred != "NA":
        spLinks.append((prevNode, dest))
        dest = prevNode
        prevNode = nodeSet[dest].pred
    return spLinks


def loadAON():
    x_bar = {l: 0.0 for l in linkSet}
    SPTT = 0.0
    for r in originZones:
        DijkstraHeap(r)
        for s in zoneSet[r].destList:
            try:
                dem = tripSet[r, s].demand
            except KeyError:
                dem = 0.0
            SPTT = SPTT + nodeSet[s].label * dem
            if r != s:
                for spLink in tracePreds(s):
                    x_bar[spLink] = x_bar[spLink] + dem
    return SPTT, x_bar


def assignment(accuracy = 0.0001, maxIter=100):
    it = 1
    gap = float("inf")
    x_bar = {l: 0.0 for l in linkSet}
    startP = time.time()
    while gap > accuracy:
        alpha = findAlpha(x_bar)
        for l in linkSet:
            linkSet[l].flow = alpha*x_bar[l] + (1-alpha)*linkSet[l].flow
        updateTravelTime()
        SPTT, x_bar = loadAON()
        TSTT = round(sum([linkSet[a].flow * linkSet[a].cost for a in linkSet]), 3)
        SPTT = round(SPTT, 3)
        gap = round(abs((TSTT / SPTT) - 1), 5)
        if it == 1:
            gap = gap + float("inf")
        it = it + 1
        if it > maxIter:
            print("The assignment did not converge with the desired gap and max iterations are reached")
            print("current gap ", gap)
            break
    print("Assignment took", time.time() - startP, " seconds")
    print("assignment converged in ", it, " iterations")


def writeresults():
    outFile = open("results.dat", "w")                                                                                                                                                                                                                                                                # IVT, WT, WK, TR
    tmpOut = "from\tto\tcapacity\tlength\tfft\ttravelTime\tflow"
    outFile.write(tmpOut+"\n")
    for i in linkSet:
        tmpOut = str(linkSet[i].tailNode) + "\t" + str(linkSet[i].headNode) + "\t" + str(linkSet[i].capacity) + "\t" + str(linkSet[i].length) + "\t" + str(linkSet[i].fft) + "\t" + str(linkSet[i].cost) + "\t" + str(linkSet[i].flow)
        outFile.write(tmpOut + "\n")
    outFile.close()

###########################################################################################################################

assignment(accuracy = 0.001, maxIter=1000)
writeresults()