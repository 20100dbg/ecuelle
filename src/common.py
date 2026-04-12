import struct
from enum import Enum
import re
import string


class Result():

    def __init__(self):
        self.query = None
        self.parameters = None
        
        self.error = None
        self.cols = None
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
        #query = re.sub("/*(.*)*/", "", query)
        return query.strip()


    @staticmethod
    def print_hex(pkt, show_line_number=False):

        def print_ascii(block):
            txt = ""
            for idx in range(0, len(block)):

                if idx == 8: txt += " "

                if chr(block[idx]) in string.printable and block[idx] not in [9,10,11,12,13]:
                    txt += chr(block[idx])
                else:
                    txt += "."

            #line = "".join([chr(b) for b in block if chr(b) in string.printable])
            return txt

        def to_hex(block):
            part1 = "".join(["{:02X} ".format(block[x]) for x in range(0, min(8, len(block)))])
            part2 = "".join(["{:02X} ".format(block[x]) for x in range(8, len(block))])
            return part1 + "  " + part2

        line = 0
        ret = ""

        for idx in range(0, len(pkt), 16):

            pkt_slice = pkt[idx:idx+16]
            empty_placeholder = ' ' * (16 - len(pkt_slice)) * 3

            if show_line_number:
                ret += f"{(line*16):08x} "

            ret += f"{to_hex(pkt_slice)}{empty_placeholder}  {print_ascii(pkt_slice)}\n"
            line += 1

        return ret + "\n"
