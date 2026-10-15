import sys
import os
import time
import socket
from _thread import start_new_thread
import random
import messages
from logger import Logger

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
        # TODO update logger calls
        self.logger = Logger(self.peerID)

        # Make subdirectory for peer
        self.directory = f"peer_{peerID}"
        os.makedirs(self.directory, exist_ok=True)

        # Bitfield Setup
        self.fileSize = int(self.commonConfig["FileSize"])
        self.pieceSize = int(self.commonConfig["PieceSize"])
        self.pieceCount = math.ceil(self.fileSize / self.pieceSize)

        numBytes = math.ceil(self.pieceCount / 8)
        self.bitfield = bytearray(numBytes)

        # Ref: set a bit in a bytearray: #2, https://www.geeksforgeeks.org/python/bitwise-algorithm-in-python/
        if self.selfInfo["hasFile"] == 1:
            for i in range(self.pieceCount):
                byteIndex = i // 8
                bitIndex = 7 - (i % 8) #left to right start w/ higher bits
                self.bitfield[byteIndex] |= (1 << bitIndex)

        # track peer activity
        self.neighborBitfields = {}
        self.peerInterested = {}
        self.neighborSockets = {}
        # TODO: TEMP to communicate
        self.chokedByNeighbor = {}

        # TCP client/socket connections
        self.startListener()
        self.connectPrevPeers()

    # TODO: Logic to end process. temp for testing
    def run(self):
        try:
            # TODO: Peers only disconnect once every peer has all the files. Fix MUCH later
            while not self.isFinished():
                time.sleep(1)
        except Exception as e:
            return

    def isFinished(self):
        return False

    def evaluateInterest(self, peerID):
        if peerID not in self.neighborBitfields:
            return False

        neighborField = self.neighborBitfields[peerID]

        # check each bit in bitfield to see if neighbor has something we dont
        for i in range(self.pieceCount):
            byteIndex = i // 8
            bitIndex = 7 - (i % 8)

            # check for index limit
            if byteIndex >= len(neighborField) or byteIndex >= len(self.bitfield):
                continue

            # check who has each bit
            neighborByte = (neighborField[byteIndex] >> bitIndex) & 1
            selfByte = (self.bitfield[byteIndex] >> bitIndex) & 1

            # if we dont have a bit but the neightbor does, record them
            if neighborByte and not selfByte:
                return True
        return False


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
        try:
            # The length of the handshake message is 32 bytes.
            rawHandshakeBytes = clientSocket.recv(32)
            recvPeerID = messages.parse_handshake_message(rawHandshakeBytes)

            # TODO: Error handling. Specific to failed peerID

            self.logger.log_connection_received(recvPeerID)

            # sendall(bytes[, flags]) notation: https://docs.python.org/3/library/socket.html
            clientSocket.sendall(messages.create_handshake_message(self.peerID))

            # TODO: Check handshake works. Temp check for message not being empty (that may be enough tbh)
            if len(self.bitfield) == 0:
                clientSocket.close()
                return

            self.neighborSockets[recvPeerID] = clientSocket
            clientSocket.sendall(messages.create_bitfield_message(bytes(self.bitfield)))
            start_new_thread(self.messageExchange, (recvPeerID, clientSocket))
        except Exception as e:
            print(f"Error handling an incoming connection: {e}")
            clientSocket.close()

    def connectPrevPeers(self):
        # Check the list of active peers. If existed beforehand, make a connection
        for peerID, info in self.peerInfo.items():
            if peerID < self.peerID:
                while True: # TODO: better way to end conneciton attempts. Likely result in infinite checks w. 1 second delays
                    try:
                        mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        mySocket.connect((info["hostname"], info["port"]))

                        self.logger.log_connection_made(peerID)

                        # The length of the handshake message is 32 bytes.
                        mySocket.sendall(messages.create_handshake_message(self.peerID))
                        recvHandshakeBytes = mySocket.recv(32)
                        recvPeerID = messages.parse_handshake_message(recvHandshakeBytes)

                        # sanity check: correct peerID, don't send incorrect info to client
                        if recvPeerID != peerID:
                            mySocket.close()
                            break

                        self.neighborSockets[recvPeerID] = mySocket
                        mySocket.sendall(messages.create_bitfield_message(bytes(self.bitfield)))
                        start_new_thread(self.messageExchange, (peerID, mySocket))
                        break
                    except socket.error:
                        time.sleep(1)

    # Helper function to select a random piece to request
    def requestMissingPiece(self, peerID):
        if peerID not in self.neighborBitfields:
            return None

        neighborField = self.neighborBitfields[peerID]
        available = []

        for i in range(self.pieceCount):
            byteIndex = i // 8
            bitIndex = 7 - (i % 8)

            neighborByte = (neighborField[byteIndex] >> bitIndex) & 1
            selfByte = (self.bitfield[byteIndex] >> bitIndex) & 1

            if neighborByte and not selfByte:
                available.append(i)

        if not available:
                return None
        return random.choice(available)

    def messageExchange(self, peerID, clientSocket):
        try:
            while True:
                # TODO: REMOVE TEMP TEST MESSAGE
                print(f"Peer {self.peerID} waiting for a message from {peerID}")

                type, payload = messages.read_message(clientSocket)

                # TODO: REMOVE TEMP TEST MESSAGE
                print(f"Peer {self.peerID}, Type {type}, Payload {payload if payload else None}")

                if type is None:
                    break

                # TODO: Finish cases for each message type
                match type:
                    case messages.Choke:
                        self.logger.log_choking(peerID)
                        self.peerInterested[peerID] = False
                    case messages.Unchoke:
                        self.logger.log_unchoking(peerID)

                        # TODO: TEMP to test message exchange
                        self.chokedByNeighbor[peerID] = False

                        piece = self.requestMissingPiece(peerID)
                        if piece is not None:
                            clientSocket.sendall(messages.create_request_message(piece))
                    case messages.Interested:
                        self.logger.log_interested_message(peerID)
                        self.peerInterested[peerID] = True

                        # TODO: TEMP to test message exchange
                        for loopID, loopSocket in self.neighborSockets.items():
                            loopSocket.sendall(messages.create_unchoke_message())
                    case messages.NotInterested:
                        self.logger.log_not_interested_message(peerID)
                        self.peerInterested[peerID] = False
                    case messages.Have:
                        pieceIndex = int.from_bytes(payload, 'big')
                        self.logger.log_have_message(peerID, pieceIndex)

                        if peerID not in self.neighborBitfields:
                            numBytes = math.ceil(self.pieceCount / 8)
                            self.neighborBitfields[peerID] = bytearray(numBytes)

                        # update what the neighbor has
                        byteIndex = pieceIndex // 8
                        bitIndex = 7 - (pieceIndex % 8) #left to right start w/ higher bits
                        self.neighborBitfields[peerID][byteIndex] |= (1 << bitIndex)

                        # check to update interest in neighbor
                        if self.evaluateInterest(peerID):
                            if not self.peerInterested.get(peerID, False):
                                self.peerInterested[peerID] = True
                                clientSocket.sendall(messages.create_interested_message())
                        else:
                            if self.peerInterested.get(peerID, False):
                                self.peerInterested[peerID] = False
                                clientSocket.sendall(messages.create_not_interested_message())


                    case messages.Bitfield:
                        self.neighborBitfields[peerID] = bytearray(payload)

                        if self.evaluateInterest(peerID):
                            self.peerInterested[peerID] = True
                            clientSocket.sendall(messages.create_interested_message())
                        else:
                            self.peerInterested[peerID] = False
                            clientSocket.sendall(messages.create_not_interested_message())

                    case messages.Request:
                        # TODO: NOT done, just temp to get some functionality

                        # find and read piece: https://www.geeksforgeeks.org/python/python-os-path-join-method/
                        index = int.from_bytes(payload, 'big')
                        size = int(self.commonConfig["PieceSize"])
                        path = os.path.join(self.directory, self.commonConfig["FileName"])

                        try:
                            # binary file reading: https://www.geeksforgeeks.org/python/python-seek-function/
                            with open(path, "rb") as f:
                                f.seek(index * size)
                                content = f.read(size)
                            clientSocket.sendall(messages.create_piece_message(index, content))
                        except Exception as e:
                            print(f"Error reading piece {index}, error: {e}")

                    case messages.Piece:
                        # TODO: NOT done, just temp to get some functionality
                        pass
                    case _:
                        print(f"Warning, message type not found, peerID: {peerID}, clientSocket: {clientSocket}")
                        pass
        except Exception as e:
            print(f"Warning, error in message exchange, peerID: {peerID}, clientSocket: {clientSocket}, exception: {e}")
        finally:
            if peerID in self.neighborSockets:
                del self.neighborSockets[peerID]
            clientSocket.close()
        return

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Incorrect amount of args to use peerProcess")
        sys.exit(1)

    peerID = int(sys.argv[1])
    process = PeerProcess(peerID)
    process.run() # stop first process from closing immediately
