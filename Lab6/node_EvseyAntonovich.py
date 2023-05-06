import random
import sched
import socket
import time
from threading import Thread
from argparse import ArgumentParser
from enum import Enum
from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCServer

PORT = 1234
CLUSTER = [1, 2, 3]
ELECTION_TIMEOUT = (6, 8)
HEARTBEAT_INTERVAL = 5


class NodeState(Enum):
    """Enumerates the three possible node states (follower, candidate, or leader)"""
    FOLLOWER = 1
    CANDIDATE = 2
    LEADER = 3


class Node:
    def __init__(self, node_id):
        """Non-blocking procedure to initialize all node parameters and start the first election timer"""
        self.node_id = node_id
        self.state = NodeState.FOLLOWER
        self.term = 0
        self.votes = {}
        self.log = []
        self.pending_entry = ''
        self.sched = sched.scheduler()
        self.commit_result = None
        self.pending_commit = False
        self.election_timer_event = self.sched.enter(random.uniform(*ELECTION_TIMEOUT), 1, self.hold_election, ())
        self.heartbeat_timer = None
        print(f"Node started! State: {self.state}. Term: {self.term}")

    def is_leader(self):
        """Returns True if this node is the elected cluster leader and False otherwise"""
        if self.state == NodeState.LEADER:
            return True
        return False

    def reset_election_timer(self):
        """Resets election timer for this (follower or candidate) node and returns it to the follower state"""
        try:
            self.sched.cancel(self.election_timer_event)
        except ValueError:
            pass
        self.election_timer_event = self.sched.enter(random.uniform(*ELECTION_TIMEOUT), 1, self.hold_election, ())
        self.state = NodeState.FOLLOWER
        return

    def hold_election(self):
        """Called when this follower node is done waiting for a message from a leader (election timeout)
            The node increments term number, becomes a candidate and votes for itself.
            Then call request_vote over RPC for all other online nodes and collects their votes.
            If the node gets the majority of votes, it becomes a leader and starts the hearbeat timer
            If the node loses the election, it returns to the follower state and resets election timer.
        """
        self.term += 1
        self.state = NodeState.CANDIDATE
        self.votes[self.term] = self.node_id
        cur_vote_count = 1
        print(f"New election term {self.term}. State: {self.state}")
        for other_node_id in CLUSTER:
            if other_node_id == self.node_id:
                continue
            try:
                print(f"Requesting vote from node {other_node_id}")
                with ServerProxy(f'http://node_{other_node_id}:{PORT}') as node:
                    node_vote = node.request_vote(self.term, self.node_id)
                    cur_vote_count += node_vote
            except socket.error as e:
                print(f"Node {other_node_id} is offline")
        if cur_vote_count > len(CLUSTER) / 2:
            self.state = NodeState.LEADER
        else:
            self.state = NodeState.FOLLOWER
            self.reset_election_timer()
        print(f"Received {cur_vote_count} votes. State: {self.state}")
        if self.is_leader():
            self.append_entries()
        return

    def request_vote(self, term, candidate_id):
        """Called remotely when a node requests voting from other nodes.
            Updates the term number if the received one is greater than `self.term`
            A node rejects the vote request if it's a leader or it already voted in this term.
            Returns True and update `self.votes` if the vote is granted to the requester candidate and False otherwise.
        """
        print(f"Got a vote request from {candidate_id} (term={term})")
        if term > self.term:
            self.term = term
        if self.state == NodeState.LEADER or self.term in self.votes.keys():
            if self.state == NodeState.LEADER:
                print(f"Didn't vote for {candidate_id} (I'm a leader)")
            else:
                print(f"Didn't vote for {candidate_id} (already voted for {self.votes[term]})")
            return False
        else:
            self.votes[self.term] = candidate_id
            print(f"Voted for {candidate_id}. Term: {term}")
            return True

    def append_entries(self):
        """Called by leader every HEARTBEAT_INTERVAL, sends a heartbeat message over RPC to all online followers.
            Accumulates ACKs from followers for a pending log entry (if any)
            If the majority of followers ACKed the entry, the entry is committed to the log and is no longer pending
        """
        print("Sending a heartbeat to followers")
        try:
            self.sched.cancel(self.heartbeat_timer)
        except Exception:
            pass
        cur_ack_count = 1
        for other_node_id in CLUSTER:
            if other_node_id == self.node_id:
                continue
            try:
                print(f"Sending heartbeat to node {other_node_id}")
                with ServerProxy(f'http://node_{other_node_id}:{PORT}') as node:
                    ack_result = node.heartbeat(self.pending_entry)
                    cur_ack_count += ack_result
                    if not ack_result:
                        print(f"Follower node {other_node_id} had heartbeat error")
            except socket.error as e:
                print(f"Follower node {other_node_id} is offline")
        self.heartbeat_timer = self.sched.enter(HEARTBEAT_INTERVAL, 1, self.append_entries, ())
        if self.pending_entry and cur_ack_count > len(CLUSTER) / 2:
            print(f"Leader committed '{self.pending_entry}'")
            self.pending_entry = ''
            if self.pending_commit:
                self.commit_result = True
            return True
        else:
            if self.pending_entry:
                print(f"Leader failed to commit '{self.pending_entry}'!")
                if self.pending_commit:
                    self.commit_result = False
                return False
            else:
                if self.pending_commit:
                    self.commit_result = True
                return True

    def heartbeat(self, leader_entry):
        """Called remotely from the leader to inform followers that it's alive and supply any pending log entry
            Followers would commit an entry if it was pending before, but is no longer now.
            Returns True to ACK the heartbeat and False on any problems.
        """
        try:
            print(f"Heartbeat received from leader (entry='{leader_entry}')")
            if leader_entry:
                self.pending_entry = leader_entry
            if self.pending_entry and not leader_entry:
                self.log.append(self.pending_entry)
                print(f"Follower committed '{self.pending_entry}'")
                self.pending_entry = ''
            self.reset_election_timer()
            return True
        except Exception as e:
            print(f"Heartbeat received from leader (entry='{leader_entry}') but failed to write it: {e}")
            return False

    def leader_receive_log(self, log):
        """Called remotely from the client. Executed only by the leader upon receiving a new log entry
            Returns True after the entry is committed to the leader log and False on any problems
        """
        print(f"Leader received log '{log}' from client")
        self.commit_result = None
        self.pending_entry = log
        self.pending_commit = True
        # Make a loop until the code writes the commit result, as we cannot return directly from a scheduled event
        while self.commit_result is None:
            time.sleep(0.01)
        result = self.commit_result
        self.commit_result = None
        self.pending_commit = False
        return result


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
            scheduler_thread = Thread(target=node.sched.run)
            scheduler_thread.start()
            server.serve_forever()
        except KeyboardInterrupt:
            pass

    pass


if __name__ == '__main__':
    main()
