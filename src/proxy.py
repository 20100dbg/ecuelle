import gevent
import logging.config
import os
import signal
import socket
import sys
import threading
import time
from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit
from common import *
from mysql import *
from postgres import *
from mssql import *

level = logging.DEBUG
log_filename = "/dev/stdout/" #"proxy.log"

#format="{asctime} - {levelname} - {message}",
logging.basicConfig(level=level, style="{", 
                    format="{asctime} [{levelname}] [{module}.{funcName}] {message}",
                    datefmt="%Y-%m-%d %H:%M",
                    filename=log_filename)


logger = logging.getLogger(__name__)


app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*',async_mode='gevent')

@app.route("/")
def main():
    tpl = open('static/main.html', 'r').read()
    response = make_response(tpl)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


class Packet():
    @staticmethod
    def init(dbms, data, previous_packet_type):
        if dbms == 'mysql' : return Mysql(data, previous_packet_type)
        elif dbms == 'postgres' : return Postgres(data, previous_packet_type)
        elif dbms == 'mssql' : return Mssql(data, previous_packet_type)
        else : return None


class Proxy():

    def __init__(self, dbms, client, server_host, server_port):
        self.dbms = dbms
        self.conn_client = client
        self.conn_server = None
        self.previous_packet_type = None
        
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

            try:
                p = Packet.init(self.dbms, data, self.previous_packet_type)
            except Exception as e:
                logger.debug(f"listen_client Exception : {e}")
                logger.debug(f"pkt={Utils.print_hex(data)}")
                p = {"result": Result()}

            if p.result.query:
                query = p.result.query
                pretty_query = Utils.clean_query(query)
                socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'query': query, 'pretty_query': pretty_query})

            if p.result.parameters:
                socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'parameters': p.result.parameters})

            if p.result.connection:
                #p.result.connection
                socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'connection': {
                    'db_name': '', 'db_version': '', 'db_version': ''
                }})


            self.previous_packet_type = p.packet_type
            self.conn_server.send(data)

        socketio.emit('msg', {'status': {'client': 'disconnected'}})
        self.conn_client.close()


    def listen_server(self, server_host, server_port):
        logger.debug(f"Server listener running")
        logger.info(f"{server_host}, {server_port}")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_host, server_port))
            self.conn_server = s
            socketio.emit('msg', {'status': {'server': 'connected'}})

            while True:
                data = s.recv(65535)
                if not data:
                    break

                try:
                    p = Packet.init(self.dbms, data, self.previous_packet_type)
                except Exception as e:
                    logger.debug(f"listen_server Exception : {e}")
                    logger.debug(f"pkt={Utils.print_hex(data)}")
                    p = {"result": Result()}

                if p.result.error or p.result.rows:
                    if p.result.error:
                        logger.debug(p.result.error)
                    socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'error': p.result.error, 
                        'result': {'cols': p.result.cols, 'rows': p.result.rows, 'nb_rows': p.result.nb_rows}})

                if p.result.connection:
                    #p.result.connection
                    socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'connection': {
                        'db_name': '', 'db_version': '', 'db_version': ''
                    }})

                if p.result.app_error:
                    socketio.emit('msg', {'timestamp': time.time(), 'dbms': self.dbms, 'app_error': p.result.app_error})

                self.previous_packet_type = p.packet_type
                self.conn_client.send(data)

            socketio.emit('msg', {'status': {'server': 'disconnected'}})



def main_loop(dbms, server_host, server_port, listening_port):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Avoid "Address already in use" in dev
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1) 

    server.bind(('0.0.0.0', listening_port))
    server.listen(1)

    while True:
        client, client_address = server.accept()

        logger.info(f"Client connected: {client_address}")
        socketio.emit('msg', {'status': {'client': 'connected'}})

        p = Proxy(dbms, client, server_host, server_port)



if not os.getenv('DB_TYPE'):
    logger.debug("Please set DB_TYPE")
    raise ValueError("Missing DB_TYPE parameter")

if not os.getenv('PROXY_PORT'):
    logger.debug("Please set PROXY_PORT")
    raise ValueError("Missing PROXY_PORT parameter")

if not os.getenv('DB_HOST'):
    logger.debug("Please set DB_HOST")
    raise ValueError("Missing DB_HOST parameter")

if not os.getenv('DB_PORT'):
    logger.debug("Please set DB_PORT")
    raise ValueError("Missing DB_PORT parameter")

dbms = os.getenv('DB_TYPE')
listening_port = int(os.getenv('PROXY_PORT'))
server_host = os.getenv('DB_HOST')
server_port = int(os.getenv('DB_PORT'))

logger.debug(f"Args - DB_TYPE={dbms}, PROXY_PORT={listening_port}, DB_HOST={server_host}, DB_PORT={server_port}")

t = threading.Thread(target=main_loop,args=[dbms, server_host, server_port, listening_port])
t.start()

