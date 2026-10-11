HandshakeHeader = "P2PFILESHARINGPROJ"
HandshakeLength = 32 #in bytes

Choke = 0
Unchoke = 1
Interested = 2
NotInterested = 3
Have = 4
Bitfield = 5
Request = 6
Piece = 7

def create_handshake_message(peerId):
    header = HandshakeHeader.encode()

    zeroBits = bytes(10)

    peerIdBytes = int(peerId).to_bytes(4, byteorder='big')

    handshake = header + zeroBits + peerIdBytes

    return handshake


def parse_handshake_message(rawHandshakeBytes):
    # checks if length doesn't match up
    if len(rawHandshakeBytes) != HandshakeLength:
        return None

    # extracts initial header value
    header = rawHandshakeBytes[:len(HandshakeHeader)].decode()

    # checks if header value doesn't match the pre-determined header value
    if header != HandshakeHeader:
        return None

    #extracts the next part to get peer id
    peerIdRawBytes = rawHandshakeBytes[28:32]

    peerId = int.from_bytes(peerIdRawBytes, byteorder='big')

    return peerId


def create_choke_message():
    messageLength = 1
    messageType = Choke

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    message = messageLengthBytes + messageTypeBytes

    return message

def create_unchoke_message():
    messageLength = 1
    messageType = Unchoke

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    message = messageLengthBytes + messageTypeBytes

    return message


def create_interested_message():
    messageLength = 1
    messageType = Interested

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    message = messageLengthBytes + messageTypeBytes

    return message

def create_not_interested_message():
    messageLength = 1
    messageType = NotInterested

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    message = messageLengthBytes + messageTypeBytes

    return message

def create_have_message(pieceIndex):
    messageLength = 5 # length in bytes
    messageType = Have

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    # different from other methods as this has to convert payload to bytes
    pieceIndexBytes = int(pieceIndex).to_bytes(4, byteorder='big')

    message = messageLengthBytes + messageTypeBytes + pieceIndexBytes

    return message

def create_bitfield_message(bitField):
    messageLength = 1 + len(bitField)
    # bitfield passed in as bytes
    messageType = Bitfield

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    message = messageLengthBytes + messageTypeBytes + bitField
    return message

def create_request_message(pieceIndex):
    messageLength = 5
    messageType = Request

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    pieceIndexBytes = int(pieceIndex).to_bytes(4, byteorder='big')

    message = messageLengthBytes + messageTypeBytes + pieceIndexBytes
    return message

def create_piece_message(pieceIndex, pieceContent):
    messageLength = 5 + len(pieceContent)
    messageType = Piece

    pieceIndexBytes = int(pieceIndex).to_bytes(4, byteorder='big')

    messageLengthBytes = messageLength.to_bytes(4, byteorder='big')
    messageTypeBytes = messageType.to_bytes(1, byteorder='big')

    #combines all variables to be returned as message
    message = messageLengthBytes + messageTypeBytes + pieceIndexBytes + pieceContent

    return message
