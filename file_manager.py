import os
import math
import shutil
import threading
from typing import Optional, Set

# manages disk i/o, piece validation, & subdir storage for p2p file sharing client
class FileManager:
    def __init__(
            self,
            peer_id: int,
            filename: str,
            file_size: int,
            piece_size: int,
            has_complete_file: bool,
            pwd: str = "."
    ):
        self.peer_id = int(peer_id)
        self.filename = filename
        self.file_size = int(file_size)
        self.piece_size = int(piece_size)
        self.has_complete_file = bool(has_complete_file)
        self.pwd = pwd

        # total num of pieces (last piece can be smaller than piece_size)
        if self.file_size > 0:
            self.piece_count = math.ceil(self.file_size / self.piece_size)
        else:
            self.piece_count = 0

        # subdirectory path: [pwd]/peer_[peer_id]/[filename]
        self.peer_dir = os.path.join(self.pwd, f"peer_{self.peer_id}")
        self.filepath = os.path.join(self.peer_dir, self.filename)
        self._lock = threading.Lock() # locking to ensure thread-safe disk access across peer connections

        self.owned_pieces = set() # track which piece indices are on current disk

        self.initialize_storage()

    # setter functions
    # creates peer_[peer_id] directory if it doesn't already exist
    # makedirs reference: https://www.geeksforgeeks.org/python/python-os-makedirs-method/
    def initialize_storage(self):
        os.makedirs(self.peer_dir, exist_ok=True)

        # fallback to copy file from root directory if it wasn't placed in peer[peer_id] yet
        if self.has_complete_file:
            root_file_path = os.path.join(self.pwd, self.filename)
            if not os.path.exists(self.filepath) and os.path.exists(root_file_path):
                shutil.copy2(root_file_path, self.filepath)

            if not os.path.exists(self.filepath):
                raise FileNotFoundError("Missing file: " + self.filepath)

            # verify file size matches Common.cfg
            actual_size = os.path.getsize(self.filepath)
            if actual_size != self.file_size:
                raise ValueError("File size mismatch for " + self.filepath)

            # seeder starts with all piece indices from 0 to piece_count -1
            self.owned_pieces = set(range(self.piece_count))
        else:
            # leecher starts with empty bin (wb mode creates or truncates the file)
            # reference: https://www.w3schools.com/python/python_file_handling.asp
            with open(self.filepath, "wb") as f:
                pass
            self.owned_pieces.clear()

    def get_piece_size(self, piece_index):
        if piece_index < 0 or piece_index >= self.piece_count:
            raise IndexError("Piece index out of range: " + str(piece_index))

        # last piece is usually smaller than piece_size, so this determines the remainder
        if piece_index == self.piece_count - 1:
            remainder = self.file_size % self.piece_size
            if remainder != 0:
                return remainder
        return self.piece_size

    def read_piece(self, piece_index):
        with self._lock: # lock disk i/o to eliminate thread conflicts
            if piece_index not in self.owned_pieces:
                return None

            # calculating exact starting byte position
            offset = piece_index * self.piece_size
            length = self.get_piece_size(piece_index)

            # open in rb mode and go directly to piece offset
            with open(self.filepath, "rb") as f:
                f.seek(offset)
                data = f.read(length)

            return data

    def write_piece(self, piece_index, data):
        size = self.get_piece_size(piece_index)
        if len(data) != size:
            raise ValueError("Invalid piece size for piece " + str(piece_index))

        with self._lock:
            # ignore duplicate pieces for already downloaded indices
            if piece_index in self.owned_pieces:
                return False

            offset = piece_index * self.piece_size

            # open in r+b mode so writing doesn't wipe any existing pieces
            with open(self.filepath, "r+b") as f:
                f.seek(offset)
                f.write(data) # write to disk
                f.flush()

            self.owned_pieces.add(piece_index)
            if len(self.owned_pieces) == self.piece_count:
                self.has_complete_file = True

            return True

    #getter functions
    def has_piece(self, piece_index):
        with self._lock:
            return piece_index in self.owned_pieces

    def get_count_owned_pieces(self):
        with self._lock:
            return len(self.owned_pieces)

    def is_complete(self):
        with self._lock:
            return len(self.owned_pieces) == self.piece_count