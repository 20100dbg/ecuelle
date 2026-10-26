import string
from enum import Enum, StrEnum, auto


class ConnectionState(Enum):
    WAIT_HANDSHAKE = auto()
    WAIT_HANDSHAKE_RESPONSE = auto()
    WAIT_HANDSHAKE_END = auto()
    READY = auto()
    WAIT_QUERY = auto()
    WAIT_QUERY_RESPONSE = auto()

class DBMS(StrEnum):
    POSTGRES = "postgres"
    MYSQL = "mysql"
    MSSQL = "mssql"
    MARIADB = "mariadb"


class Result:

    def __init__(self):
        self.query = None
        self.parameters = None
        
        self.error = None
        self.cols = None
        self.rows = None
        self.nb_rows = None

        self.connection = {}
        self.app_error = None
        

class Utils:

    @staticmethod
    def rev(data):
        return data[::-1]

    @staticmethod  
    def to_hex(data):
        if type(data) is int:
            return data            
        return " ".join([f"{x:02X}" for x in data])

    @staticmethod
    def clean_query(query):
        #query = re.sub("/*(.*)*/", "", query)
        return query.strip()

    @staticmethod
    def hex(pkt):
        if isinstance(pkt, int):
            return pkt.to_bytes(1, "big")
        return "".join([f"{x:02X} " for x in pkt])

    @staticmethod
    def print_hex(pkt, show_line_number=False):

        def print_ascii(block):
            txt = ""
            for idx in range(len(block)):

                if idx == 8: txt += " "

                if chr(block[idx]) in string.printable and block[idx] not in [9,10,11,12,13]:
                    txt += chr(block[idx])
                else:
                    txt += "."

            #line = "".join([chr(b) for b in block if chr(b) in string.printable])
            return txt

        def to_hex(block):
            part1 = "".join([f"{block[x]:02X} " for x in range(min(8, len(block)))])
            part2 = "".join([f"{block[x]:02X} " for x in range(8, len(block))])
            return part1 + "  " + part2

        ret = ""

        for idx in range(0, len(pkt), 16):
            pkt_slice = pkt[idx:idx+16]
            empty_placeholder = ' ' * (16 - len(pkt_slice)) * 3

            if show_line_number:
                ret += f"{idx:08x} "

            ret += f"{to_hex(pkt_slice)}{empty_placeholder}  {print_ascii(pkt_slice)}\n"
        return ret + "\n"
