import sqlite3
from concurrent.futures import ThreadPoolExecutor

import grpc
import schema_pb2 as stub
import schema_pb2_grpc as service


SERVER_ADDR = '0.0.0.0:1234'


class Database(service.DatabaseServicer):
    def PutUser(self, request, context):
        print(f"PutUser({request.user_id}, '{request.user_name}')")
        try:
            conn = sqlite3.connect("db.sqlite")
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)", (request.user_id, request.user_name))
            conn.commit()
            return stub.BoolResponse(status=True)
        except:
            return stub.BoolResponse(status=False)

    def GetUsers(self, request, context):
        print("GetUsers()")
        conn = sqlite3.connect("db.sqlite")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users")
        rows = cursor.fetchall()
        users = []
        for row in rows:
            user = stub.User(user_id=row[0], user_name=row[1])
            users.append(user)
        resp = stub.UsersResponse(users=users)
        return resp

    def DeleteUser(self, request, context):
        conn = sqlite3.connect("db.sqlite")
        print(f"DeleteUser({request.user_id})")
        try:
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM Users WHERE id={request.user_id}")
            conn.commit()
            return stub.BoolResponse(status=True)
        except:
            return stub.BoolResponse(status=False)


def main():
    conn = sqlite3.connect("db.sqlite")
    print(sqlite3.version)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS Users")
    create_table_sql = """ CREATE TABLE Users (
                                        id integer PRIMARY KEY,
                                        name text
                                    ); """
    c.execute(create_table_sql)
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    service.add_DatabaseServicer_to_server(
        Database(), server)
    server.add_insecure_port(SERVER_ADDR)
    server.start()
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Terminating...")
    conn.close()


if __name__ == '__main__':
    main()
