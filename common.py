import struct
from enum import Enum

class Dbms(Enum):
    MySQL = "mysql"
    PostgreSQL = "postgres"

class Result():

    def __init__(self):
        self.connection_info = None
        
        self.query = None
        self.parameters = None
        
        self.error = None
        self.rows = None
        self.affected_rows = None

        self.info = None
        

class Utils():

    @staticmethod  
    def to_hex(data):
        if type(data) is int:
            return data
            
        return " ".join(["{:02X}".format(x) for x in data])
