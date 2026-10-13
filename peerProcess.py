import sys
import os
import time
import datetime
import socket
import threading
from _thread import start_new_thread

import messages

# remove if bitfield stuff is removed from init
import math

def loadConfig(filepath="Common.cfg"):
    config = {}
    # Python file notation: https://www.geeksforgeeks.org/python/how-to-read-from-a-file-in-python/
    with open(filepath, "r") as f:
        for line in f:
            pairs = line.strip().split()
            if len(pairs) == 2:
                key, val = pairs
                # Val's are strings. Must specify int elsewhere
                config[key] = val
            else:
                print(f"Error: Invalid configuration info on Common.cfg")
                return "-1"
    return config

def loadPeerInfo(selfID, filepath="PeerInfo.cfg"):
    peers = {}
    selfInfo = {}
    with open(filepath, "r") as f:
        for line in f:
            peerInfo = line.strip().split()
            if len(peerInfo) == 4:
                peerID = int(peerInfo[0])
                peers[peerID] = {"hostname": peerInfo[1], "port": int(peerInfo[2]), "hasFile": int(peerInfo[3])}
                if peerID == selfID:
                    selfInfo = peers[peerID]
            else:
                print(f"Error: Invalid peer info on PeerInfo.cfg")
                return "-1", "-1"
    return selfInfo, peers

class peerLogger:
    def __init__(self, peerID):
        self.logFilename = f"log_peer_{peerID}.log"

    def log(self, msg):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.logFilename, "a") as f:
            f.write(f"{timestamp}: {msg}\n")

class PeerProcess:
    def __init__(self, peerID):
        # setup peer and read config files
        self.peerID = peerID
        self.commonConfig = loadConfig()
        self.selfInfo, self.peerInfo = loadPeerInfo(peerID)

        # Error return on loading either config file. Print statement will clarify which/why
        if self.peerID == "-1" or self.selfInfo == "-1":
            sys.exit(1)

        # Use peerLogger class to init log file and log messages
        self.logger = peerLogger(self.peerID)

        # Make subdirectory for peer
        self.directory = f"peer_{peerID}"
        os.makedirs(self.directory, exist_ok=True)

        # Bitfield Setup
        self.fileSize = int(self.commonConfig["FileSize"])
        self.pieceSize = int(self.commonConfig["PieceSize"])
        self.pieceCount = math.ceil(self.fileSize / self.pieceSize)
        # TODO: Figure out what's sent to bitfield.py, and what's done here
        '''
        if (self.selfInfo["hasFile"] == 1):
            self.bitfield =
        else :
        '''

        # TODO: Remove placeholder log test once other logs are setup
        self.logger.log(f"Peer test init. peer {peerID}. TESTING REMOVE")

        # TCP client/socket connections
        # track active connections, start listener, connect to existing peers
        self.startListener()
        self.connectPrevPeers()

    def startListener(self):
        # Chapter 3 (Page 194) Recommends threading for socket connections.
        # tldr, Use 1 process, create a new thread with a new connection socket for each client connection
        def listenerThread():
            # Uses textbook exampleon page 156, and geeksforgeeks for python translation
            # https://www.geeksforgeeks.org/python/socket-programming-multi-threading-python/
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            mySocket.bind((self.selfInfo["hostname"], self.selfInfo["port"]))
            mySocket.listen()

            while True:
                clientSocket, address = mySocket.accept()
                start_new_thread(self.incomingConnection, (clientSocket,))

        # starts a new thread for each client. Use _threat built in feature
        start_new_thread(listenerThread, ())

    def incomingConnection(self, clientSocket):
        # TODO: listener thread will call, handle logic here
        return

    def connectPrevPeers(self):
        # Check the list of active peers. If existed beforehand, make a connection
        for peerID, info in self.peerInfo.items():
            if peerID < self.peerID:
                while True:
                    # TODO: Error handling. Prob try loop everything in the 'while True'

                    mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    mySocket.connect((info["hostname"], info["port"]))

                    # TODO: Handshake

                    # TODO: Log connection

                    # TODO: Message exchange thread. peer-peer messages
                    start_new_thread(self.messageExchange, (peerID, mySocket))

    def messageExchange(self, peerID, clientSocket):
        # TODO: message exchange after thread created to exchange between peers
        return

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Incorrect amount of args to use peerProcess")
        sys.exit(1)

    peerID = int(sys.argv[1])
    process = PeerProcess(peerID)
