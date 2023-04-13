import json

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'


def main():
    credentials = PlainCredentials(RMQ_USER, RMQ_PASS)
    parameters = ConnectionParameters(credentials=credentials, host=RMQ_HOST, heartbeat=600)
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    try:
        while True:
            user_input = input("Enter Query: ")
            bytes_object = user_input.encode()
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=f'rep.{user_input}', body=bytes_object)

    except KeyboardInterrupt:
        pass
    connection.close()


if __name__ == '__main__':
    main()
