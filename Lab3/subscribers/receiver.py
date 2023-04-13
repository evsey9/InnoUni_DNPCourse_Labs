import json

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'co2.*'
THRESHOLD = 500


def callback(channel, method, properties, body):
    json_string = body.decode("utf-8")
    json_dict = json.loads(json_string)
    print(f'{json_dict["time"]}: ', end='')
    if json_dict["value"] > THRESHOLD:
        print("WARNING")
    else:
        print("OK")
    with open("receiver.log", "a") as f:
        f.write(json_string)
        f.write('\n')


def main():
    credentials = PlainCredentials(RMQ_USER, RMQ_PASS)
    parameters = ConnectionParameters(credentials=credentials, host=RMQ_HOST)
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare("co2")
    channel.queue_bind("co2", EXCHANGE_NAME, ROUTING_KEY)
    channel.basic_consume("co2", callback, auto_ack=True)
    try:
        print("[*] Waiting for CO2 data. Press CTRL+C to exit")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()


if __name__ == '__main__':
    main()
