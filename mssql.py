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
        pass


    class FieldType(Enum):
        FIELD_TYPE_TINY = 1
        FIELD_TYPE_SHORT = 2
        FIELD_TYPE_LONG = 3
        FIELD_TYPE_FLOAT = 4
        FIELD_TYPE_DOUBLE = 5
        FIELD_TYPE_TIMESTAMP = 7
        FIELD_TYPE_LONGLONG = 8
        FIELD_TYPE_INT24 = 9
        FIELD_TYPE_DATE = 10
        FIELD_TYPE_TIME = 11
        FIELD_TYPE_DATETIME = 12
        FIELD_TYPE_YEAR = 13
        FIELD_TYPE_UNKNOWN = 245
        FIELD_TYPE_NEWDECIMAL = 246
        FIELD_TYPE_BLOB = 252
        FIELD_TYPE_VAR_STRING = 253
        FIELD_TYPE_STRING = 254


    class PacketType(Enum):
        PACKET_COMPLETION = 0x43
        PACKET_DATA_ROW = 0x44
        PACKET_QUERY = 0x51
        PACKET_AUTH_REQUEST = 0x52
        PACKET_ROW_DESCRIPTION = 0x54
        PACKET_TERMINATION = 0x58
        PACKET_SASL_RESPONSE = 0x70
