import sys
import os
import time
import datetime

def loadConfig(filepath="Common.cfg"):
    config = {}
    # Slight reminder on file notation: https://www.geeksforgeeks.org/python/how-to-read-from-a-file-in-python/
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

        # use peerLogger class to init log file and log messages
        self.logger = peerLogger(self.peerID)

        # Make subdirectory for peer
        self.directory = f"log_peer_{peerID}"
        os.makedirs(self.directory, exist_ok=True)

        # Bitfield stuff. Idk
        ''''# TODO: Ensure vals exist
        self.fileSize = self.selfInfo["FileSize"]
        self.pieceSize = self.selfInfo["PieceSize"]
        self.pieceCount = ()
        
        if self.selfInfo["hasFile"] == 1:
            self.bitfield = self.'''

        # TODO: Remove placeholder log test once other logs are setup
        self.logger.log(f"Peer test init. peer {peerID}. TESTING REMOVE")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Incorrect amount of args to use peerProcess")
        sys.exit(1)

    peerID = int(sys.argv[1])
    process = PeerProcess(peerID)
