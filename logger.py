import os
import time, datetime

class Logger:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.log_file_path = f"log_peer_{peer_id}.log"
        #Initialize file or check for existence
        with open(self.log_file_path, "w") as f:
            pass

    def get_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def write_log(self, message):
        timestamp = self.get_timestamp()
        try:
            with open(self.log_file_path, "a") as f:
                f.write(f"[{timestamp}]: {message}\n")
            return True
        except Exception as e:
            print(f"Error with writing log: {e}")
            return False
            

    def log_connection_made(self, other_peer_id):
        message = f"Peer {self.peer_id} makes a connection to Peer {other_peer_id}."
        return self.write_log(message)

    def log_connection_received(self, other_peer_id):
        message = f"Peer {self.peer_id} is connected from Peer {other_peer_id}."
        return self.write_log(message)

    def log_change_preferred_neighbor(self, preferred_neighbor_list):
        message = f"Peer {self.peer_id} has the preferred neighbors {preferred_neighbor_list}."
        return self.write_log(message)

    def log_change_optimistic_unchoke(self, neighbor_id):
        message = f"Peer {self.peer_id} has the optimistically unchoked neighbor {neighbor_id}."
        return self.write_log(message)

    def log_unchoking(self, other_peer_id):
        message = f"Peer {self.peer_id} is unchoked by {other_peer_id}."
        return self.write_log(message)

    def log_choking(self, other_peer_id):
        message = f"Peer {self.peer_id} is choked by {other_peer_id}."
        return self.write_log(message)

    def log_have_message(self, other_peer_id, piece_index):
        message = f"Peer {self.peer_id} received the 'have' message from {other_peer_id} for the piece {piece_index}."
        return self.write_log(message)

    def log_interested_message(self, other_peer_id):
        message = f"Peer {self.peer_id} received the 'interested' message from {other_peer_id}."
        return self.write_log(message)

    def log_not_interested_message(self, other_peer_id):
        message = f"Peer {self.peer_id} received the 'not interested' message from {other_peer_id}."
        return self.write_log(message)

    def log_downloading_piece(self, other_peer_id, piece_index, num_pieces):
        message = f"Peer {self.peer_id} has downloaded the piece {piece_index} from {other_peer_id}. Now the number of pieces it has is {num_pieces}."
        return self.write_log(message)

    def log_completed_download(self):
        message = f"Peer {self.peer_id} has downloaded the complete file."
        return self.write_log(message)