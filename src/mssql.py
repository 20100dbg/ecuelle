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


    def print_debug(self, txt):
        if self.debug:
            print(f"{txt}")


    def parse_packet(self, pkt):
        pass
        #Utils.print_hex(pkt)


    class FieldType(Enum):
        FIELD_TYPE_TINY = 1
        

    class PacketType(Enum):
        PACKET_COMPLETION = 0x43
        
