import struct
from common import *
from enum import Enum
import logging
import sys, traceback
logger = logging.getLogger(__name__)

class Mssql():

    def __init__(self, pkt, previous_packet):
        self.pkt = pkt
        self.result = Result()
        self.debug = True
        self.packet_type = None
        self.previous_packet = previous_packet

        try:
            self.parse_packet(pkt)
        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            logger.debug(f"parse_packet Exception : {e}")
            logger.debug(f"pkt={Utils.print_hex(pkt)}")


    def parse_packet(self, pkt):
        self.packet_type = self.get_packet_type(pkt)

        logger.debug(f"self.packet_type={self.packet_type}")

        if self.packet_type == Mssql.PacketType.PACKET_BATCH:
            self.parse_BATCH(pkt)

        elif self.packet_type == Mssql.PacketType.PACKET_RESPONSE and \
            self.previous_packet == Mssql.PacketType.PACKET_BATCH:
            self.parse_RESPONSE(pkt)


    def get_packet_type(self, pkt):

        if pkt[0] in [packet_type.value for packet_type in Mssql.PacketType]:
            return Mssql.PacketType(pkt[0])

        return Mssql.PacketType.PACKET_UNKNOWN


    def parse_BATCH(self, pkt):
        status = pkt[1]
        packet_length = int.from_bytes(pkt[2:4], "big")
        channel = int.from_bytes(pkt[4:6], "big")
        packet_number = pkt[6]
        window = pkt[7]
        headers_length = int.from_bytes(pkt[8:12], "little")
        idx = packet_length - (packet_length - headers_length - 8)

        self.result.query = pkt[idx:].decode()

    def parse_RESPONSE(self, pkt):
        if pkt[8] == 0x81:
            self.parse_results(pkt)
        elif pkt[8] == 0xaa:
            self.parse_error(pkt)
        else:
            print("Unkown packet")


    def parse_error(self, pkt):
        token_length = int.from_bytes(pkt[9:10], "little")
        sql_error_number = int.from_bytes(pkt[11:15], "little")
        state = pkt[15]
        severity = pkt[16]
        message_length = int.from_bytes(pkt[17:19], "little")
        message = pkt[19:19+(message_length*2)]

        self.result.error = message.decode()


    def parse_results(self, pkt):
        status = pkt[1]
        packet_length = int.from_bytes(pkt[2:4], "big")
        channel = int.from_bytes(pkt[4:6], "big")
        packet_number = pkt[6]
        window = pkt[7]

        nb_columns = int.from_bytes(pkt[9:11], "little")
        result = []

        print(f"nb_columns = {nb_columns}")

        idx = 11
        fields = []

        row_count = int.from_bytes(pkt[-8:], "little")
        print(f"row_count = {row_count}")
        print()

        for _ in range(nb_columns):

            #usertype = pkt[idx:idx+4]
            #flags = pkt[idx+4:idx+6]
            type = pkt[idx+6]
            type_size = pkt[idx+7]

            if type not in [packet_type.value for packet_type in Mssql.FieldType]:
                logger.debug(f"type unknown ({type})")


            if type in [Mssql.FieldType.FIELD_TYPE_BIT.value,
                        Mssql.FieldType.FIELD_TYPE_INT.value,
                        Mssql.FieldType.FIELD_TYPE_FLOAT.value,
                        Mssql.FieldType.FIELD_TYPE_MONEY.value,
                        Mssql.FieldType.FIELD_TYPE_TIME.value,
                        Mssql.FieldType.FIELD_TYPE_DATETIME.value,
                        Mssql.FieldType.FIELD_TYPE_DATETIME2.value,
                        Mssql.FieldType.FIELD_TYPE_DATETIMEOFFSET.value,
                        Mssql.FieldType.FIELD_TYPE_XML.value,
                        Mssql.FieldType.FIELD_TYPE_GUID.value]:
                idx += 8

            elif type in [Mssql.FieldType.FIELD_TYPE_DECIMAL.value,
                         Mssql.FieldType.FIELD_TYPE_NUMERIC.value]:
                idx += 10

            elif type in [Mssql.FieldType.FIELD_TYPE_DATE.value,
                          Mssql.FieldType.FIELD_TYPE_INT4.value]:
                idx += 7

            elif type in [Mssql.FieldType.FIELD_TYPE_BIGCHAR.value,
                          Mssql.FieldType.FIELD_TYPE_BIGVARCHAR.value,
                          Mssql.FieldType.FIELD_TYPE_NCHAR.value,
                          Mssql.FieldType.FIELD_TYPE_NVARCHAR.value]:
                idx += 14

            elif type in [Mssql.FieldType.FIELD_TYPE_TEXT.value,
                          Mssql.FieldType.FIELD_TYPE_NTEXT.value]:
                idx += 27

            elif type in [Mssql.FieldType.FIELD_TYPE_BIGBINARY.value,
                          Mssql.FieldType.FIELD_TYPE_BIGVARBIN.value]:
                idx += 9

            elif type == Mssql.FieldType.FIELD_TYPE_SSVARIANT.value:
                idx += 11

            elif type == Mssql.FieldType.FIELD_TYPE_IMAGE.value:
                idx += 12
                table_name_length = int.from_bytes(pkt[idx:idx+2], "little")
                table_name = pkt[idx+2:idx+2+(table_name_length*2)].decode()
                idx += 2+(table_name_length*2)


            name_length = pkt[idx]
            idx += 1
            name = pkt[idx:idx+(name_length*2)]
            idx += name_length*2

            fields.append({'name': name, 'type': type, 'size': type_size})
            print(f"name = {name.decode()}")

        while True:

            if idx > len(pkt):
                break

            if pkt[idx] == 0xfd:
                break

            idx += 1

            print(Utils.hex(pkt[idx:idx+20]))

            row = []
            for i in range(len(fields)):

                print(Mssql.FieldType(fields[i]['type']))

                if fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_BIT.value,
                                         Mssql.FieldType.FIELD_TYPE_INT.value
                                        ]:
                    field_length = pkt[idx]
                    print(f"bit/int field_length={field_length}")
                    field_value = int.from_bytes(pkt[idx+1:idx+1+field_length], "little")
                    idx += 1

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_DECIMAL.value, 
                                           Mssql.FieldType.FIELD_TYPE_NUMERIC.value]:
                    field_length = 4
                    sign = pkt[idx+1]

                    field_value = struct.unpack("<i", pkt[idx+2:idx+2+field_length])[0] / 100
                    idx += 2

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_FLOAT.value,
                                           Mssql.FieldType.FIELD_TYPE_MONEY.value,
                                          ]:
                    field_length = fields[i]['size']
                    print(f"{Utils.hex(pkt[idx+1:idx+1+field_length])}")

                    if field_length == 4:
                        field_value = struct.unpack("<f", pkt[idx+1:idx+1+field_length])[0]
                    elif field_length == 8:
                        field_value = struct.unpack("<d", pkt[idx+1:idx+1+field_length])[0]

                    idx += 1

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_DATE.value]:
                    field_length = pkt[idx]
                    #09/04/2026
                    field_value = Utils.hex(pkt[idx+1:idx+1+field_length])
                    idx += 1

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_TIME.value]:
                    field_length = pkt[idx]
                    #52200.0000000 seconds
                    field_value = Utils.hex(pkt[idx+1:idx+1+field_length])
                    idx += 1

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_DATETIME.value,
                                           Mssql.FieldType.FIELD_TYPE_DATETIME2.value,
                                           Mssql.FieldType.FIELD_TYPE_DATETIMEOFFSET.value]:
                    field_length = pkt[idx]
                    #2026-09-04 16:30:54
                    field_value = Utils.hex(pkt[idx+1:idx+1+field_length])
                    idx += 1

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_BIGCHAR.value,
                                           Mssql.FieldType.FIELD_TYPE_BIGVARCHAR.value,
                                          ]:
                    field_length = int.from_bytes(pkt[idx:idx+2], "little")
                    field_value = pkt[idx+2:idx+2+field_length]
                    idx += 2

                else:
                    field_length = 0
                    field_value = ""



                print(f"field_value={field_value}")
                print()
                idx += field_length
                row.append(field_value)


            result.append(row)

        self.result.cols = fields
        self.result.rows = result


    class FieldType(Enum):
        FIELD_TYPE_IMAGE = 34
        FIELD_TYPE_TEXT = 35
        FIELD_TYPE_GUID = 36
        FIELD_TYPE_INT = 38
        FIELD_TYPE_DATE = 40
        FIELD_TYPE_TIME = 41
        FIELD_TYPE_DATETIME2 = 42
        FIELD_TYPE_DATETIMEOFFSET = 43
        FIELD_TYPE_INT4 = 56
        FIELD_TYPE_SSVARIANT = 98
        FIELD_TYPE_NTEXT = 99
        FIELD_TYPE_BIT = 104
        FIELD_TYPE_DECIMAL = 106
        FIELD_TYPE_NUMERIC = 108
        FIELD_TYPE_FLOAT = 109
        FIELD_TYPE_MONEY = 110
        FIELD_TYPE_DATETIME = 111
        FIELD_TYPE_BIGVARBIN = 165
        FIELD_TYPE_BIGVARCHAR = 167
        FIELD_TYPE_BIGBINARY = 173
        FIELD_TYPE_BIGCHAR = 175
        FIELD_TYPE_NVARCHAR = 231
        FIELD_TYPE_NCHAR = 239
        FIELD_TYPE_XML = 241
        

    class PacketType(Enum):
        PACKET_BATCH = 0x01
        PACKET_RESPONSE = 0x04
        PACKET_TM_REQUEST = 0x0e
        PACKET_PRELOGIN = 0x12
        PACKET_UNKNOWN = 0xff
        
