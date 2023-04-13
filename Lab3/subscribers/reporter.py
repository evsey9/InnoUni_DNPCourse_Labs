import json
import os
from datetime import datetime

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exchange_type import ExchangeType

RMQ_HOST = 'localhost'
RMQ_USER = 'rabbit'
RMQ_PASS = '1234'
EXCHANGE_NAME = 'amq.topic'
ROUTING_KEY = 'rep.*'


def callback(channel, method, properties, body):
    user_string = body.decode("utf-8")
    try:
        with open("receiver.log", "r") as f:
            json_objects = []
            lines = f.readlines()
            for line in lines:
                line.strip()
                if len(line) <= 2:
                    continue
                json_dict = json.loads(line)
                json_objects.append(json_dict)
            if user_string == "current" or user_string == "average":
                time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                print(f'{time}: ', end='')
                if len(json_objects) == 0:
                    print("No sensor readings found!")
            if user_string == "current":
                print(f"Latest CO2 level is {json_objects[-1]['value']}")
            elif user_string == "average":
                sum_of_values = 0
                for cur_json_dict in json_objects:
                    sum_of_values += cur_json_dict["value"]
                print(f"Average CO2 level is {sum_of_values / len(json_objects)}")
            else:
                pass
    except FileNotFoundError:
        time = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
        print(f'{time}: ', end='')
        print("No sensor readings found!")


def main():
    credentials = PlainCredentials(RMQ_USER, RMQ_PASS)
    parameters = ConnectionParameters(credentials=credentials, host=RMQ_HOST)
    connection = BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare("reports")
    channel.queue_bind("reports", EXCHANGE_NAME, ROUTING_KEY)
    channel.basic_consume("reports", callback, auto_ack=True)
    try:
        print("[*] Waiting for reports. Press CTRL+C to exit")
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    connection.close()


if __name__ == '__main__':
    main()
