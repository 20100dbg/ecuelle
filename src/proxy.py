import gevent
from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit
import time
import threading
import os
import logging.config
import socket
import sys
import time
from common import *
from mysql import *
from postgres import *
from mssql import *

level = logging.DEBUG
log_filename = "proxy.log"

logging.basicConfig(level=level, style="{", format="{asctime} - {levelname} - {message}",
                    datefmt="%Y-%m-%d %H:%M",
                    filename=log_filename)

logger = logging.getLogger(__name__)


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*',async_mode='gevent')

global count
count = 0


@app.route("/")
def main():
    tpl = open('main.html', 'r').read()
    response = make_response(tpl)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

@socketio.on('request')
def request(params):
    global count
    count += 1
    socketio.emit('result', {'data': count})


class Packet():
    @staticmethod
    def init(dbms, data, previous_packet):
        if dbms == 'mysql' : return Mysql(data, previous_packet)
        elif dbms == 'postgres' : return Postgres(data, previous_packet)
        elif dbms == 'mssql' : return Mssql(data, previous_packet)
        else : return None


class Proxy():

    def __init__(self, dbms, client, server_host, server_port):
        self.dbms = dbms
        self.conn_client = client
        self.conn_server = None
        self.previous_packet = None
        
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

            p = Packet.init(self.dbms, data, self.previous_packet)
            logger.info(f"C -> S : {p.packet_type}")

            if p.result.query:
                query = p.result.query
                pretty_query = Utils.clean_query(query)
                socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'query': query, 'pretty_query': pretty_query})

            if p.result.parameters:
                socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'parameters': p.result.parameters})

            if p.result.info:
                socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'info': p.result.info})

            self.previous_packet = p.packet_type
            self.conn_server.send(data)
            
        self.conn_client.close()


    def listen_server(self, server_host, server_port):
        logger.debug(f"Server listener running")
        logger.info(f"{server_host}, {server_port}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_host, server_port))
            self.conn_server = s

            while True:
                data = s.recv(65535)
                if not data:
                    break

                p = Packet.init(self.dbms, data, self.previous_packet)
                logger.info(f"C <- S : {p.packet_type}")

                if p.result.error or p.result.rows:
                    socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'error': p.result.error, 'result': {'cols': p.result.cols, 'rows': p.result.rows}})

                if p.result.info:
                    socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'info': p.result.info})

                self.previous_packet = p.packet_type
                self.conn_client.send(data)



def main_loop(dbms, server_host, server_port, listening_port):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Avoid "Address already in use" in dev
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1) 

    server.bind(('0.0.0.0', listening_port))
    server.listen(1)

    while True:
        client, client_address = server.accept()
        logger.info(f"Client connected: {client}, {client_address}")

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

logger.debug(f"Args - DB_TYPE={dbms}, PROXY_PORT={listening_port}, SERVER_HOST={server_host}, SERVER_PORT={server_port}")

t = threading.Thread(target=main_loop,args=[dbms, server_host, server_port, listening_port])
t.start()


