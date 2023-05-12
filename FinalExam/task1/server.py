import json
import socket


PORT = 50000


class RR:
    def __init__(self, type, key, value):
        self.type = type
        self.key = key
        self.value = value


class DNS_Server:
    def __init__(self):
        self.ip_dict = {
            ('A', 'example.com'): RR('A', 'example.com', '1.2.3.4'),
            ('PTR', '1.2.3.4'): RR('PTR', '1.2.3.4', 'example.com')
        }
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 50000))

    def run(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            query = json.loads(data.decode())
            if query['type'] == 'A':
                key = (query['type'], query['key'])
            elif query['type'] == 'PTR':
                key = (query['type'], query['key'])
            elif query['type'] == 'CNAME':
                key = (query['type'], query['key'])
            else:
                response = {'type': 'error', 'value': 'Invalid query type'}
                self.sock.sendto(json.dumps(response).encode(), addr)
                continue
            if key in self.ip_dict:
                response = {'type': self.ip_dict[key].type, 'key': self.ip_dict[key].key, 'value': self.ip_dict[key].value}
                self.sock.sendto(json.dumps(response).encode(), addr)
            else:
                query['value'] = 'NXDOMAIN'
                self.sock.sendto(json.dumps(query).encode(), addr)


def main():
    records_list = {
        ('A', 'example.com'): RR('A', 'example.com', '1.2.3.4'),
        ('PTR', '1.2.3.4'): RR('PTR', '1.2.3.4', 'example.com')
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', PORT))
    print(f"Server: listening on 0.0.0.0:{PORT}")
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            query = json.loads(data.decode())
            print(f"Client: {query}")
            if query['type'] in ['A', 'PTR', 'CNAME']:
                key = (query['type'], query['key'])
            else:
                print(f"Server: Record not found. Sending error.")
                query['value'] = 'NXDOMAIN'
                sock.sendto(json.dumps(query).encode(), addr)
                continue
            if key in records_list.keys():
                print(f"Server: Record found. Sending answer.")
                response = {'type': records_list[key].type, 'key': records_list[key].key, 'value': records_list[key].value}
                sock.sendto(json.dumps(response).encode(), addr)
            else:
                print(f"Server: Record not found. Sending error.")
                query['value'] = 'NXDOMAIN'
                sock.sendto(json.dumps(query).encode(), addr)
    except KeyboardInterrupt:
        print("Shutting down...")


if __name__ == '__main__':
    main()
