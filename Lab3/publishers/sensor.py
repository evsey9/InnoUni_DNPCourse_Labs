import json
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'co2.sensor'


def main():
    credentials = PlainCredentials(RMQ_USER, RMQ_PASS)
    parameters = ConnectionParameters(credentials=credentials, host=RMQ_HOST, heartbeat=600)
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    try:
        while True:
            co2_level = int(input("Enter CO2 level: "))
            time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            dict_object = {
                "time": time,
                "value": co2_level
            }
            json_string = json.dumps(dict_object, indent=None)
            json_bytes = json_string.encode()
            channel.basic_publish(exchange=EXCHANGE_NAME, routing_key=ROUTING_KEY, body=json_bytes)

    except KeyboardInterrupt:
        pass
    connection.close()


if __name__ == '__main__':
    main()
