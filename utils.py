import struct

class Utils():

    @staticmethod  
    def to_hex(data):
        if type(data) is int:
            return data
            
        return " ".join(["{:02X}".format(x) for x in data])
