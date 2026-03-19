import gevent
from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit
import time
import threading
import os

import socket
import sys
import time
from common import *
from mysql import *
from postgres import *
from mssql import *


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*',async_mode='gevent')

@app.route("/")
def main():
    tpl = open('main.html', 'r').read()
    response = make_response(tpl)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


def send_query(query, result, status):

    timestamp = time.time()

    socketio.emit('receive_query', {'query': query, 'result': result, 'status': status, 'timestamp': timestamp})


#Can be called from JS
"""
@socketio.on('call_server')
def process_data(params):
    data_id = int(params['id'])
    data_str = params['str']
"""


class Packet():
    @staticmethod
    def init(dbms, data):
        if dbms == 'mysql' : return Mysql(data)
        elif dbms == 'postgres' : return Postgres(data)
        elif dbms == 'mssql' : return Mssql(data)
        else : return None


class Proxy():

    def __init__(self, dbms, client, server_host, server_port):
        self.dbms = dbms
        self.conn_client = client
        self.conn_server = None
        
        t = threading.Thread(target=self.listen_server,args=[server_host, server_port])
        t.start()

        time.sleep(0.1)

        t = threading.Thread(target=self.listen_client,args=[])
        t.start()


    def listen_client(self):
        
        while True:
            data = self.conn_client.recv(65535)
            if not data:
                break

            Utils.print_hex(data)

            p = Packet.init(self.dbms, data)
            print(f"C -> S : {p.packet_type}")

            if p.result.query:
                query = p.result.query
                pretty_query = Utils.clean_query(query)
                socketio.emit('receive_query', {'timestamp': time.time(), 'dbms': self.dbms, 'query': query, 'pretty_query': pretty_query})

            if p.result.parameters:
                #print(p.result.parameters)
                socketio.emit('receive_query', {'timestamp': time.time(), 'dbms': self.dbms, 'parameters': p.result.parameters})

            if p.result.info:
                #print(p.result.info)
                socketio.emit('receive_query', {'timestamp': time.time(), 'dbms': self.dbms, 'info': p.result.info})


            print()
            self.conn_server.send(data)
            
        self.conn_client.close()


    def listen_server(self, server_host, server_port):

        print(server_host, server_port)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_host, server_port))
            self.conn_server = s

            print("connected to server")

            while True:
                data = s.recv(65535)
                if not data:
                    break

                p = Packet.init(self.dbms, data)

                print(f"C <- S : {p.packet_type}")

                if p.result.error:
                    #print(p.result.error)
                    socketio.emit('receive_query', {'timestamp': time.time(), 'dbms': self.dbms, 'error': p.result.error})

                if p.result.rows:
                    #print(p.result.rows)
                    socketio.emit('receive_query', {'timestamp': time.time(), 'dbms': self.dbms, 'result': p.result.rows})

                if p.result.nb_rows:
                    #print(p.result.nb_rows)
                    socketio.emit('receive_query', {'timestamp': time.time(), 'dbms': self.dbms, 'nb_rows': p.result.nb_rows})

                if p.result.info:
                    #print(p.result.info)
                    socketio.emit('receive_query', {'timestamp': time.time(), 'dbms': self.dbms, 'info': p.result.info})


                print()
                self.conn_client.send(data)



def main_loop(dbms, server_host, server_port, listening_port):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Avoid "Address already in use" in dev
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1) 

    server.bind(('0.0.0.0', listening_port))
    server.listen(1)

    while True:
        client, client_address = server.accept()
        p = Proxy(dbms, client, server_host, server_port)


"""
parser = argparse.ArgumentParser(description='MySQL/Postgres/MSSQL proxy')
parser.add_argument('-s', '--server_host', metavar='', required=False, default='127.0.0.1', help='DB server IP or hostname')
parser.add_argument('-p', '--server_port', metavar='', type=int, required=True, help='DB server port')
#parser.add_argument('-l', '--listening_port', metavar='', type=int, required=True, help='Listening port waiting for clients')
#parser.add_argument('-d', '--dbms', metavar='', required=True, choices=dbms, default='mysql', help='DBMS')
args = parser.parse_args()
"""


dbms = os.getenv('DB_TYPE')
listening_port = int(os.getenv('PROXY_PORT'))
server_host = os.getenv('SERVER_HOST')
server_port = int(os.getenv('SERVER_PORT'))

t = threading.Thread(target=main_loop,args=[dbms, server_host, server_port, listening_port])
t.start()


