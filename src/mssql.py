import struct
from common import *
from enum import Enum
import logging
import sys, traceback
logger = logging.getLogger(__name__)

class Mssql():

    def __init__(self, pkt):
        self.pkt = pkt
        self.result = Result()
        self.debug = True
        self.packet_type = None

        try:
            self.parse_packet(pkt)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            logger.debug(f"parse_packet Exception : {e}")
            logger.debug(f"pkt={Utils.print_hex(pkt)}")


    def parse_packet(self, pkt):
        self.packet_type = self.get_packet_type(pkt)

        if self.packet_type == Mssql.PacketType.PACKET_BATCH:
            self.parse_BATCH(pkt)


    def get_packet_type(self, pkt):

        if pkt[0] in [packet_type.value for packet_type in Mssql.PacketType]:
            return Mssql.PacketType(pkt[0])

        return Mssql.PacketType.PACKET_UNKNOWN


    def parse_BATCH(self, pkt):
        status = pkt[1]
        packet_length = int.from_bytes(pkt[2:4], "big")
        channel = int.from_bytes(pkt[4:6], "big")
        packet_number = pkt[6]
        


    class FieldType(Enum):
        FIELD_TYPE_TINY = 1
        

    class PacketType(Enum):
        PACKET_BATCH = 0x01
        PACKET_RESPONSE = 0x04
        PACKET_TM_REQUEST = 0x0e
        PACKET_PRELOGIN = 0x12
        PACKET_UNKNOWN = 0xff
        
