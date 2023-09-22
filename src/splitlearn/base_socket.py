import socket
import hashlib
from helper import NoneException

# Constants
ACK = b"ACK"
NACK = b"NACK"
EOF = b"EOF"
RETRY_LIMIT = 1000


class BaseSocket:  # TODO refactor this abse socket
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def _compute_checksum(self, data: bytes) -> bytes:
        """Compute and return the MD5 checksum of the given data."""
        return hashlib.md5(data).digest()

    def _send_data(self, data: bytes):
        """Send data with checksum and handle ACK/NACK."""
        retries = 0
        while retries < RETRY_LIMIT:
            try:
                checksum = self._compute_checksum(data)
                self.server_socket.sendall(checksum + data + EOF)
                ack = self.server_socket.recv(len(ACK))
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
                    chunk = self.server_socket.recv(4096)
                    if EOF in chunk:
                        data.extend(chunk[:-len(EOF)])
                        break
                    data.extend(chunk)

                received_checksum = data[:16]
                actual_data = data[16:]

                if self._compute_checksum(actual_data) == received_checksum:
                    self.server_socket.sendall(ACK)
                    return actual_data
                else:
                    self.server_socket.sendall(NACK)
                    print("Checksum mismatch while receiving data. Retrying...")
                    retries += 1
            except socket.timeout:
                print("Socket timeout. Reinitializing...")
                retries += 1
            except socket.error as e:
                print(f"Error receiving data: {e}")
                retries += 1

        if retries == RETRY_LIMIT:
            print("Failed to receive data after multiple retries.")
        return data

    def close_connection(self):
        """Close the socket if it exists."""
        if hasattr(self, 'server_socket') and self.server_socket:
            self.server_socket.close()
