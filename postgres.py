import struct
from common import *
from enum import Enum

class Postgres():

    def __init__(self, pkt):
        self.pkt = pkt
        self.result = Result()
        self.debug = True
        self.packet_type = None

        try:
            self.parse_packet(pkt)
        except Exception as e:
            print(e)


    def print_debug(self, txt):
        if self.debug:
            print(f"{txt}")


    def parse_packet(self, pkt):

        #self.packet_type = self.get_packet_type(packet_number, payload_length, payload)

        self.packet_type = Postgres.PacketType(pkt[0])


        if self.packet_type == Postgres.PacketType.PACKET_QUERY:
            payload_length = int.from_bytes(pkt[1:5], "big")
            self.result.query = pkt[5:-1].decode()

        elif self.packet_type == Postgres.PacketType.PACKET_ROW_DESCRIPTION:
            self.parse_ROW_DESCRIPTION(pkt)



    def parse_ROW_DESCRIPTION(self, pkt):
        payload_length = int.from_bytes(pkt[1:5], "big")
        field_count = int.from_bytes(pkt[5:7], "big")
        idx = 7
        field_names = []
        rows = []

        for _ in range(field_count):
            idx2 = pkt.find(0, idx)
            column_name = pkt[idx:idx2]

            field_names.append(column_name)
            #print(f"column_name {column_name}")
            idx = idx2 + 19


        while pkt[idx] == Postgres.PacketType.PACKET_DATA_ROW.value:
            payload_length = int.from_bytes(pkt[idx+1:idx+5], "big")
            field_count = int.from_bytes(pkt[idx+5:idx+7], "big")
            idx += 7

            row = []

            for _ in range(field_count):
                column_length = int.from_bytes(pkt[idx:idx+4], "big")
                data = pkt[idx+4:idx+4+column_length].decode()

                row.append(data)
                idx += 4 + column_length

            rows.append(row)

        self.result.rows = rows

    def get_packet_type(self, pkt):


        if pkt[0] == 0:
            payload_length = int.from_bytes(pkt[0:4], "big")
            
            payload = pkt[4:payload_length - 4]
            request_code = int.from_bytes(payload, "big")
            if request_code == 80877103:
                print("SSL_RESPONSE")


        elif len(pkt) == 1 and pkt[0] == 0x4e:
            print("SSL_RESPONSE")
            pass


        else:
            return Postgres.PacketType(pkt[0])


    class PacketType(Enum):
        PACKET_COMPLETION = 0x43
        PACKET_DATA_ROW = 0x44
        PACKET_QUERY = 0x51
        PACKET_AUTH_REQUEST = 0x52
        PACKET_ROW_DESCRIPTION = 0x54
        PACKET_TERMINATION = 0x58
        PACKET_SASL_RESPONSE = 0x70
