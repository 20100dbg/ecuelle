import struct
from common import *
from enum import Enum

class Mssql():

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
        pass


    class FieldType(Enum):
        FIELD_TYPE_TINY = 1
        

    class PacketType(Enum):
        PACKET_COMPLETION = 0x43
        
