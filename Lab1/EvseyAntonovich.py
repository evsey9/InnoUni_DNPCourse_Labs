import argparse
import socket
import os

BUFFER_SIZE = 20480
IP = "0.0.0.0"


def get_seqno(seqno_received) -> int:
	return (seqno_received + 1) % 2


def construct_ack_message(seqno_received) -> bytes:
	return "a|{}".format(get_seqno(seqno_received)).encode()


class Session:
	def __init__(self, addr):
		self.addr = addr
		self.filename = None
		self.filesize = None
		self.file_handle = None
		self.last_seqno = None
		self.bytes_received = 0


def main():
	parser = argparse.ArgumentParser(
		prog='StopAndWaitARQ',
		description='UDP ARQ implementation')
	parser.add_argument('port', type=int)
	args = parser.parse_args()
	port = int(args.port)
	with socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) as sock:
		sessions = {}
		sock.bind((IP, port))
		print("Server: Listening on IP and port {}:{}...".format(IP, port))
		while True:
			finished_flag = False
			data, addr = sock.recvfrom(BUFFER_SIZE)
			cur_session = None
			message_type = data[0:1].decode()
			message_seqno = int(data[2:3].decode())
			print("\nServer: Received message from address {} of type {} and seqno {}.".format(addr, message_type, message_seqno))
			if addr in sessions.keys():
				cur_session = sessions[addr]
			if cur_session is None or message_seqno != cur_session.last_seqno:
				# Make sure that we have not received and processed this packet already
				if message_type == 's':
					# Check if this is the starting message
					print("Server: Message is a start message.")
					if cur_session is not None:
						# Check if this address is new or not
						print("Server: Stopping writing for old file {}.".format(cur_session.filename))
						cur_session.file_handle.close()
					cur_session = Session(addr)
					sessions[addr] = cur_session
					filename_and_filesize = data[4:].decode().split('|')
					cur_session.filename = filename_and_filesize[0]
					cur_session.filesize = int(filename_and_filesize[1])
					if os.path.isfile(cur_session.filename):
						print("Server: File {} already exists, overwriting.".format(cur_session.filename))
					cur_session.file_handle = open(cur_session.filename, "wb")
					print("Server: Starting new session for address {} with filename {} and filesize {}.".format(cur_session.addr, cur_session.filename, cur_session.filesize))

				if message_type == 'd' and cur_session is not None:
					print("Server: Message is a data message.")
					binary_data = data[4:]
					cur_session.file_handle.write(binary_data)
					cur_session.bytes_received += len(binary_data)
					print("Server: Wrote {} bytes to {}.".format(len(binary_data), cur_session.filename))
					if cur_session.bytes_received >= cur_session.filesize:
						print("Server: Finished receiving {}.".format(cur_session.filename))
						cur_session.file_handle.close()
						sessions.pop(addr)
						finished_flag = True

				if message_type != 's' and message_type != 'd':
					for key in sessions.keys():
						sessions[key].file_handle.close()
					raise ValueError("Invalid message type!")

			if cur_session is not None:
				if cur_session.last_seqno == message_seqno:
					print("Server: Message has been already processed")
				else:
					cur_session.last_seqno = message_seqno

			ack_message = construct_ack_message(message_seqno)
			sock.sendto(ack_message, addr)
			print("Finished processing message and sent acknowledgement message {} to {}.".format(ack_message.decode(), addr))
			if finished_flag:
				print("\n\n")


if __name__ == "__main__":
	main()
