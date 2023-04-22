from argparse import ArgumentParser
from bisect import bisect_left
from threading import Thread
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

M = 5
PORT = 1234
RING = [2, 7, 11, 17, 22, 27]


class Node:
    def __init__(self, node_id):
        """Initializes the node properties and constructs the finger table according to the Chord formula"""
        self.id = node_id
        self.finger_table = [self.get_successor_iteratively((self.id + 2 ** i) % (2 ** M)) for i in range(M)]
        self.successor = self.get_successor_iteratively((self.id + 1) % (2 ** M))
        self.data = dict()
        print(f"Node created! Finger table = {self.finger_table}")

    def get_successor_iteratively(self, node_id):
        if node_id == self.id:
            return self.id
        if node_id > RING[-1]:
            return RING[0]
        for i_node in RING:
            if i_node >= node_id:
                return i_node

    def closest_preceding_node(self, id):
        """Returns node_id of the closest preceeding node (from n.finger_table) for a given id"""
        for i in range(M - 1, -1, -1):
            if self.id <= id and self.id < self.finger_table[i] < id \
                    or self.id > id and (self.id < self.finger_table[i] or self.finger_table[i] < id):
                return self.finger_table[i]
        return self.id

    def find_successor(self, id):
        """Recursive function returning the identifier of the node responsible for a given id"""
        if id == self.id:
            print(f"Finalizing request (key={id}) at self node {id}")
            return id

        if self.id <= self.successor and self.id < id <= self.successor \
                or self.id > self.successor and (self.id < id or id <= self.successor):
            print(f"Finalizing request (key={id}) at successor node {self.successor}")
            return self.successor
        n0 = self.closest_preceding_node(id)

        with ServerProxy(f'http://node_{n0}:{PORT}') as node_n0:
            print(f"Forwarding request (key={id}) to node {n0}")
            return node_n0.find_successor(id)

    def put(self, key, value):
        """Stores the given key-value pair in the node responsible for it"""
        print(f"put({key}, {value})")
        target_node = self.find_successor(key)
        # print(f"Found node {target_node}. Inserting key {key}...")
        try:
            if target_node != self.id:
                with ServerProxy(f'http://node_{target_node}:{PORT}') as target_node_proxy:
                    ret_value = target_node_proxy.store_item(key, value)
                    # print(f"At node {target_node} inserted key {key} with {ret_value} success!")
                    return ret_value
            else:
                ret_value = self.store_item(key, value)
                # print(f"At node {target_node} inserted key {key} with {ret_value} success!")
                return ret_value
        except Exception:
            pass
        # print(f"At node {target_node} failed to insert key {key}!")
        return False

    def get(self, key):
        """Gets the value for a given key from the node responsible for it"""
        print(f"get({key})")
        target_node = self.find_successor(key)
        try:
            if target_node != self.id:
                with ServerProxy(f'http://node_{target_node}:{PORT}') as target_node_proxy:
                    return target_node_proxy.retrieve_item(key)
            else:
                return self.retrieve_item(key)
        except Exception:
            pass
        return -1

    def store_item(self, key, value):
        """Stores a key-value pair into the data store of this node"""
        try:
            self.data[key] = value
            return True
        except Exception:
            pass
        return False

    def retrieve_item(self, key):
        """Retrieves a value for a given key from the data store of this node"""
        try:
            return self.data[key]
        except Exception:
            pass
        return -1


def main():
    with SimpleXMLRPCServer(('0.0.0.0', PORT), logRequests=False) as server:
        try:
            parser = ArgumentParser()
            parser.add_argument('node_id', type=int)
            args = parser.parse_args()
            node_id = args.node_id
            node = Node(node_id)
            server.register_introspection_functions()
            server.register_instance(node)
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
