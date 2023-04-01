import os
import socket
import time

from PIL import Image

# Import multithreading/queue
from threading import Thread
import queue
from queue import Queue

# Import multiprocessing
from multiprocessing import Pool

# Define constants
SERVER_URL = '127.0.0.1:1234'
FILE_NAME = 'EvseyAntonovich.gif'
CLIENT_BUFFER = 1024
FRAME_COUNT = 5000
N_THREADS = 32

q = Queue(0)


def get_frame(frame_index):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        ip, port = SERVER_URL.split(':')
        s.connect((ip, int(port)))
        image = b''
        while True:
            packet = s.recv(CLIENT_BUFFER)
            if not packet:
                break
            image += packet
        with open(f'frames/{frame_index}.png', 'wb') as f:
            f.write(image)


class ClientThread(Thread):
    def __init__(self, name=None):
        super().__init__(name=name)

    def run(self):
        while True:
            try:
                task = q.get(block=False)
                print(f"Thread {self.name}: working on frame {task}.")
            except queue.Empty:
                print(f"Thread {self.name}: all work done. Exiting.")
                break
            else:
                get_frame(task)
                print(f"Thread {self.name}: finished frame {task}.")
                q.task_done()


def download_frames():
    t0 = time.time()
    if not os.path.exists('frames'):
        os.mkdir('frames')
    for i in range(FRAME_COUNT):
        q.put(i)
    threads = [ClientThread() for _ in range(N_THREADS)]
    [t.start() for t in threads]
    q.join()
    return time.time() - t0


def open_frame(frame_id):
    return Image.open(f"frames/{frame_id}.png").convert("RGBA")


def create_gif():
    t0 = time.time()
    frames_in = [frame_id for frame_id in range(FRAME_COUNT)]
    with Pool() as p:
        frames_out = p.map(open_frame, frames_in)
    frames_out[0].save(FILE_NAME, format="GIF",
                   append_images=frames_out[1:], save_all=True, duration=500, loop=0)
    return time.time() - t0


if __name__ == '__main__':
    print(f"Frames download time: {download_frames()}")
    print(f"GIF creation time: {create_gif()}")

# Before multithreading and multiprocessing:
# Frames download time: 4.0299999713897705
# GIF creation time: 13.649999141693115


# after multithreading:
# Frames download time: 1.4830012321472168
# GIF creation time: 13.848997592926025


# after multiprocessing:
# Frames download time: 1.4189999103546143
# GIF creation time: 5.190000534057617
