import json
import socket


PORT = 50000


class Query:
    def __init__(self, type, key):
        self.type = type
        self.key = key


def main():
    queries = [
        Query(type='A', key='example.com'),
        Query(type='PTR', key='1.2.3.4'),
        Query(type='CNAME', key='moodle.com')
    ]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for query in queries:
        print(f"Client: Sending query for {query.key}")
        sock.sendto(json.dumps(query.__dict__).encode(), ('localhost', PORT))
        data, addr = sock.recvfrom(1024)
        response = json.loads(data.decode())
        print(f"Server: {response}")


if __name__ == '__main__':
    main()
