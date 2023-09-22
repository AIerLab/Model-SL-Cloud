import socket
import time
from typing import Any
import hashlib
from helper import NoneException
from helper import IN_QUEUE, OUT_QUEUE, CONDITION

# Predefined constants for communication
ACK = b"ACK"
NACK = b"NACK"
EOF = b"EOF"
RETRY_LIMIT = 1000


class SplitSocket:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.initialize_socket()

    def initialize_socket(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.host, self.port)
        try:
            self.server_socket.bind(server_address)
            self.server_socket.listen(1)
            self.client_socket, client_address = self.server_socket.accept()
            print('client connected:', client_address)
            # Setting a timeout of 2 seconds
            self.server_socket.settimeout(10)
        except Exception as e:
            print(f"Error with socket operation: {e}")
            self.close_connection()
            time.sleep(1.0)
            self.initialize_socket()

    def _compute_checksum(self, data: bytes) -> bytes:
        """Compute and return the MD5 checksum of the given data."""
        return hashlib.md5(data).digest()

    def receive_data(self) -> Any:
        """Receives data and pushes it into the data_queue."""
        CONDITION.acquire()
        data = self._receive_data()
        print(f"[SERVER]: Received data.")

        data = {"byte_data": data}
        IN_QUEUE.put(data)
        CONDITION.notify()

        CONDITION.wait()
        data = OUT_QUEUE.get()
        self._send_data(data["byte_data"])

        print(f"[SERVER]: Send data back.")
        # CONDITION.release()  # Uncomment this if you want to release the condition

    def _send_data(self, data: bytes):
        """Send data with checksum and handle ACK/NACK."""
        retries = 0
        while retries < RETRY_LIMIT:
            try:
                checksum = self._compute_checksum(data)
                self.client_socket.sendall(checksum + data + EOF)
                ack = self.client_socket.recv(len(ACK))
                if ack == ACK:
                    break
                else:
                    print("Checksum mismatch while sending data. Retrying...")
                    retries += 1
            except socket.timeout:
                print("Timeout while waiting for ACK. Retrying...")
                retries += 1
            except socket.error as e:
                print(f"Error sending data: {e}")
                retries += 1

        if retries == RETRY_LIMIT:
            print("Failed to send data after multiple retries.")

    def _receive_data(self) -> bytes:
        """Receive data, validate its checksum, and return the data."""
        data = bytearray()
        retries = 0
        while retries < RETRY_LIMIT:
            try:
                while True:
                    chunk = self.client_socket.recv(4096)
                    if EOF in chunk:
                        data.extend(chunk[:-len(EOF)])
                        break
                    data.extend(chunk)

                received_checksum = data[:16]
                actual_data = data[16:]

                if self._compute_checksum(actual_data) == received_checksum:
                    self.client_socket.sendall(ACK)
                    if actual_data == b"":
                        raise NoneException("None received")
                    return actual_data
                else:
                    self.client_socket.sendall(NACK)
                    print("Checksum mismatch while receiving data. Retrying...")
                    retries += 1
            except socket.timeout:
                print("Socket timeout. Reinitializing...")
                self.close_connection()
                self.initialize_socket()
                return self._receive_data()  # Optionally retry receiving
            except socket.error as e:
                print(f"Error receiving data: {e}")
                retries += 1

        if retries == RETRY_LIMIT:
            print("Failed to receive data after multiple retries.")

        if data == b"":
            raise NoneException("None received")
        return data

    def run(self) -> None:
        """Main loop to continuously receive data."""
        while True:
            self.receive_data()

    def close_connection(self):
        """Close the client socket if it exists."""
        if self.client_socket:
            self.client_socket.close()

# import socket
# import time
# from typing import Any
# from helper import NoneException, IN_QUEUE, OUT_QUEUE, CONDITION
# from .base_socket import BaseSocket, ACK, NACK, EOF, RETRY_LIMIT


# class SplitSocket(BaseSocket):
#     def __init__(self, host: str, port: int):
#         super().__init__(host, port)
#         self.initialize_socket()

#     def initialize_socket(self):
#         self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         server_address = (self.host, self.port)
#         try:
#             self.server_socket.bind(server_address)
#             self.server_socket.listen(1)
#             self.client_socket, client_address = self.server_socket.accept()
#             print('client connected:', client_address)
#             # Setting a timeout of 2 seconds
#             self.server_socket.settimeout(10)
#         except Exception as e:
#             print(f"Error with socket operation: {e}")
#             self.close_connection()
#             time.sleep(1.0)
#             self.initialize_socket()

#     def receive_data(self) -> Any:
#         """Receives data and pushes it into the data_queue."""
#         CONDITION.acquire()
#         data = self._receive_data()
#         print(f"[SERVER]: Received data.")

#         data = {"byte_data": data}
#         IN_QUEUE.put(data)
#         CONDITION.notify()

#         CONDITION.wait()
#         data = OUT_QUEUE.get()
#         self._send_data(data["byte_data"])

#         print(f"[SERVER]: Sent data back.")
#         CONDITION.release()

#     def run(self) -> None:
#         """Main loop to continuously receive data."""
#         while True:
#             self.receive_data()
