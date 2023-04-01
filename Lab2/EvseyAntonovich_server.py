import socket
import threading
from threading import Thread
import os
import io

from PIL import Image

IP_ADDR = '127.0.0.1'
PORT = 1234
SERVER_BUFFER = 1024


def generate_random_image(size=(10, 10)):
    rand_image = Image.new('RGB', size)

    def random_pixels():
        return os.urandom(size[0] * size[1])

    pixels = zip(random_pixels(), random_pixels(), random_pixels())
    rand_image.putdata(list(pixels))
    return rand_image


class ServerThread(Thread):
    def __init__(self, conn, addr, name=None):
        super().__init__(name=name)
        self.conn = conn
        self.addr = addr

    def run(self):
        image = generate_random_image()
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        with self.conn:
            self.conn.send(img_byte_arr)
        print(f"Sent an image to {self.addr}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((IP_ADDR, PORT))
        server_socket.listen()
        while True:
            try:
                print("Server: Waiting for a new connection")
                conn, addr = server_socket.accept()
                print(f"Server: Accepted conn req from {addr}")
                thread = ServerThread(conn, addr)
                thread.start()
                print(f"Server: Started thread for {addr}")
            except KeyboardInterrupt:
                print("Server: Exiting...")
                exit()
            except:
                print(f"Server: Error...")
                exit()


if __name__ == "__main__":
    main()
