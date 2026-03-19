import struct
from enum import Enum
import re
import string


class Result():

    def __init__(self):
        self.query = None
        self.parameters = None
        
        self.error = None
        self.rows = None
        self.nb_rows = None

        self.info = None
        

class Utils():

    @staticmethod  
    def to_hex(data):
        if type(data) is int:
            return data            
        return " ".join(["{:02X}".format(x) for x in data])

    @staticmethod
    def clean_query(query):
        query = re.sub("/*(.*)*/", "", query)
        return query.strip()


    @staticmethod
    def print_hex(pkt):

        def print_ascii(block):
            txt = ""
            for idx in range(0, len(block)):

                if idx == 8: txt += " "

                if chr(block[idx]) in string.printable:
                    txt += chr(block[idx])
                else:
                    txt += "."

            #line = "".join([chr(b) for b in block if chr(b) in string.printable])
            return txt

        def to_hex(block):
            part1 = "".join(["{:02X} ".format(block[x]) for x in range(0, 8)])
            part2 = "".join(["{:02X} ".format(block[x]) for x in range(8, 16)])
            return part1 + "  " + part2

        line = 0

        for idx in range(0, len(pkt), 16):

            pkt_slice = pkt[idx:idx+16]

            if len(pkt_slice) < 16:
                pkt_slice = pkt_slice + ((16 -len(pkt_slice)) * b' ')

            #{(line*16):08x}
            print(f"{to_hex(pkt_slice)}  {print_ascii(pkt_slice)}")

            line += 1

