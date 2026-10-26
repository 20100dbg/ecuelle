import struct
from common import *
from enum import Enum
import logging
import sys, traceback
import datetime
logger = logging.getLogger(__name__)

class Mssql():

    def __init__(self, pkt, connection_state):
        self.result = Result()
        self.packet_type = None
        self.connection_state = connection_state
        self.channel = 0

        self.parse_header(pkt, connection_state)
        self.parse_packet(pkt)

    def parse_header(self, pkt, connection_state):
        self.packet_type = self.get_packet_type(pkt)
        status = pkt[1]
        packet_length = int.from_bytes(pkt[2:4], "big")
        self.channel = int.from_bytes(pkt[4:5], "big")

    def parse_packet(self, pkt):
        if self.packet_type == Mssql.PacketType.PACKET_BATCH:
            self.connection_state = ConnectionState.WAIT_QUERY_RESPONSE
            self.parse_BATCH(pkt)

        elif self.packet_type == Mssql.PacketType.PACKET_RESPONSE:

            if self.connection_state in [ConnectionState.WAIT_HANDSHAKE_END, ConnectionState.WAIT_QUERY_RESPONSE, ConnectionState.READY]:
                #self.connection_state = ConnectionState.READY
                self.parse_RESPONSE(pkt)

            if self.connection_state == ConnectionState.WAIT_HANDSHAKE_RESPONSE:
                self.connection_state = ConnectionState.WAIT_HANDSHAKE_END


        elif self.packet_type == Mssql.PacketType.PACKET_PRELOGIN and self.connection_state != ConnectionState.WAIT_HANDSHAKE_END:
            self.connection_state = ConnectionState.WAIT_HANDSHAKE_RESPONSE


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

        idx = 8
        payload_length = int.from_bytes(pkt[2:4], "little")

        while idx < payload_length - 1:
            token_type = pkt[idx]

            if token_type == 0x81:
                token_length = int.from_bytes(pkt[idx+1:idx+3], "little")
                idx += 3
                self.parse_results(pkt)
                break
            elif token_type == 0xaa:
                token_length = int.from_bytes(pkt[idx+1:idx+3], "little")
                idx += 3
                self.parse_error(pkt)
                break
            elif token_type == 0xe3: #EnvChange
                token_length = int.from_bytes(pkt[idx+1:idx+3], "little")
                idx += 3
                envchange_type = pkt[idx]

                if envchange_type  == 1: #Database
                    new_value_length = pkt[idx+1]
                    new_value = pkt[idx+2:idx+2+(new_value_length*2)].decode('utf-16')
                    self.result.connection['schema'] = new_value

            elif token_type == 0xad: #LoginAck
                token_length = int.from_bytes(pkt[idx+1:idx+3], "little")
                idx += 3
                envchange_type = pkt[idx]
                server_name_length = pkt[idx+5]
                server_name = pkt[idx+6:idx+6+(server_name_length*2)].decode('utf-16')

                server_version = pkt[idx+6+(server_name_length*2):idx+6+(server_name_length*2)+4]
                server_version = f"{server_version[0]}.{server_version[1]}.{int.from_bytes(server_version[2:4], 'big')}"

                self.result.connection['db_version'] = server_version

            elif token_type == 0xae: #FeatureExtAct
                token_length = int.from_bytes(pkt[idx+2:idx+6], "little")
                idx += 7
            elif token_type == 0xe4: #Session state
                token_length = int.from_bytes(pkt[idx+1:idx+5], "little")
                idx += 5
            elif token_type == 0xfd: #Done
                token_length = int.from_bytes(pkt[idx+1:idx+3], "little")
                idx += 3
                break
            elif token_type == 0xab: #Info
                token_length = int.from_bytes(pkt[idx+1:idx+3], "little")
                idx += 3
            else:
                logger.debug(f"Unknown packet, token_type={hex(token_type)} {token_type}")

            idx += token_length


    def parse_error(self, pkt):
        token_length = int.from_bytes(pkt[9:10], "little")
        sql_error_number = int.from_bytes(pkt[11:15], "little")
        state = pkt[15]
        severity = pkt[16]
        message_length = int.from_bytes(pkt[17:19], "little")
        message = pkt[19:19+(message_length*2)].decode('utf-16')
        self.result.error = {'code': '', 'state': state, 'message': message}


    def parse_results(self, pkt):
        status = pkt[1]
        packet_length = int.from_bytes(pkt[2:4], "big")
        channel = int.from_bytes(pkt[4:6], "big")
        packet_number = pkt[6]
        window = pkt[7]

        nb_columns = int.from_bytes(pkt[9:11], "little")
        result = []

        idx = 11
        fields = []

        row_count = int.from_bytes(pkt[-8:], "little")

        for _ in range(nb_columns):

            #usertype = pkt[idx:idx+4]
            #flags = pkt[idx+4:idx+6]
            field_type = pkt[idx+6]
            type_size = 0
            scale = precision = table_name = None

            if field_type not in [packet_type.value for packet_type in Mssql.FieldType]:
                logger.debug(f"type unknown ({field_type})")

            if field_type in [Mssql.FieldType.FIELD_TYPE_BIT.value,
                        Mssql.FieldType.FIELD_TYPE_INT.value,
                        Mssql.FieldType.FIELD_TYPE_FLOAT.value,
                        Mssql.FieldType.FIELD_TYPE_MONEY.value,
                        Mssql.FieldType.FIELD_TYPE_DATETIME.value,
                        Mssql.FieldType.FIELD_TYPE_XML.value,
                        Mssql.FieldType.FIELD_TYPE_GUID.value]:
                type_size = pkt[idx+7]
                idx += 8

            elif field_type in [Mssql.FieldType.FIELD_TYPE_TIME.value,
                          Mssql.FieldType.FIELD_TYPE_DATETIME2.value,
                          Mssql.FieldType.FIELD_TYPE_DATETIMEOFFSET.value,
                          ]:
                scale = pkt[idx+7]
                idx += 8

            elif field_type in [Mssql.FieldType.FIELD_TYPE_DECIMAL.value,
                         Mssql.FieldType.FIELD_TYPE_NUMERIC.value]:
                type_size = pkt[idx+7]
                precision = pkt[idx+8]
                scale = pkt[idx+9]
                idx += 10

            elif field_type in [Mssql.FieldType.FIELD_TYPE_INT4.value]:
                type_size = pkt[idx+7]
                idx += 7

            elif field_type in [Mssql.FieldType.FIELD_TYPE_DATE.value]:
                idx += 7

            elif field_type in [Mssql.FieldType.FIELD_TYPE_BIGCHAR.value,
                          Mssql.FieldType.FIELD_TYPE_BIGVARCHAR.value,
                          Mssql.FieldType.FIELD_TYPE_NCHAR.value,
                          Mssql.FieldType.FIELD_TYPE_NVARCHAR.value]:
                type_size = int.from_bytes(pkt[idx+7:idx+9], "little")
                idx += 14

            elif field_type in [Mssql.FieldType.FIELD_TYPE_TEXT.value,
                          Mssql.FieldType.FIELD_TYPE_NTEXT.value]:
                type_size = int.from_bytes(pkt[idx+7:idx+11], "little")
                idx += 27

            elif field_type in [Mssql.FieldType.FIELD_TYPE_BIGBINARY.value,
                          Mssql.FieldType.FIELD_TYPE_BIGVARBIN.value]:
                type_size = int.from_bytes(pkt[idx+7:idx+9], "little")
                idx += 9

            elif field_type == Mssql.FieldType.FIELD_TYPE_SSVARIANT.value:
                idx += 11

            elif field_type == Mssql.FieldType.FIELD_TYPE_IMAGE.value:
                type_size = int.from_bytes(pkt[idx+7:idx+11], "little")
                idx += 12
                table_name_length = int.from_bytes(pkt[idx:idx+2], "little")
                table_name = pkt[idx+2:idx+2+(table_name_length*2)].decode()
                idx += 2+(table_name_length*2)


            name_length = pkt[idx]
            idx += 1
            name = pkt[idx:idx+(name_length*2)].decode()
            idx += name_length*2

            data = {'name': name, 'type': field_type, 'size': type_size}
            if scale: data['scale'] = scale
            if precision: data['precision'] = precision
            
            fields.append(data)

        while True:

            if idx >= len(pkt) or \
                (idx+4 == len(pkt) and pkt[idx:] == b"\x00\x00\x00\x00") or \
                pkt[idx] == 0xfd:
                break

            idx += 1

            row = []
            for i in range(len(fields)):

                if fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_BIT.value,
                                         Mssql.FieldType.FIELD_TYPE_INT.value
                                        ]:
                    field_length = pkt[idx]
                    field_value = int.from_bytes(pkt[idx+1:idx+1+field_length], "little")
                    idx += 1

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_INT4.value]:
                    field_length = 4
                    field_value = int.from_bytes(pkt[idx:idx+field_length], "little")

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_DECIMAL.value, 
                                           Mssql.FieldType.FIELD_TYPE_NUMERIC.value]:
                    field_length = 4
                    sign = pkt[idx+1]
                    field_value = struct.unpack("<i", pkt[idx+2:idx+2+field_length])[0] / 100
                    idx += 2

                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_FLOAT.value:
                    field_length = pkt[idx]
                    field_length = fields[i]['size']

                    if field_length == 4:
                        field_value = struct.unpack("<f", pkt[idx+1:idx+1+field_length])[0]
                    elif field_length == 8:
                        field_value = struct.unpack("<d", pkt[idx+1:idx+1+field_length])[0]

                    idx += 1
                
                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_MONEY.value:
                    field_length = pkt[idx]
                    field_length = fields[i]['size']
                    idx += 1

                    if field_length == 8:
                        idx += 4
                        field_length = 4

                    field_value = struct.unpack("<I", pkt[idx:idx+field_length])[0] / 10000


                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_DATE.value]:
                    field_length = pkt[idx]

                    tmp = pkt[idx+1:idx+1+field_length]
                    days = int.from_bytes(tmp, byteorder='little', signed=False)
                    field_value = datetime.date(1, 1, 1) + datetime.timedelta(days=days)
                    field_value = str(field_value)
                    idx += 1

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_TIME.value]:
                    field_length = pkt[idx]
                    seconds = int.from_bytes(pkt[idx+1:idx+1+field_length], "little") / 10000000
                    seconds = int(seconds)
                    field_value = datetime.timedelta(seconds=seconds)
                    field_value = str(field_value)
                    idx += 1

                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_DATETIME.value:
                    field_length = pkt[idx]
                    idx += 1

                    if field_length == 8:
                        days = int.from_bytes(pkt[idx:idx+4], byteorder='little', signed=False)
                        time_units = int.from_bytes(pkt[idx+4:idx+8], byteorder='little', signed=False)
                        seconds = time_units / 300.0
                        field_value = datetime.datetime(1900, 1, 1) + datetime.timedelta(days=days, seconds=seconds)
                    
                    elif field_length == 4:
                        days = int.from_bytes(pkt[idx:idx+2], byteorder='little', signed=False)
                        minutes = int.from_bytes(pkt[idx+2:idx+4], byteorder='little', signed=False)
                        field_value = datetime.datetime(1900, 1, 1) + datetime.timedelta(days=days, minutes=minutes)

                    field_value = str(field_value)

                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_DATETIME2.value:
                    field_length = pkt[idx]
                    idx += 1

                    time_length = field_length - 3
                    time_units = pkt[idx:idx+time_length]
                    days = pkt[idx+time_length:idx+field_length]

                    time_units = int.from_bytes(time_units, byteorder='little', signed=False)
                    seconds = time_units / (10 ** fields[i]['scale'])

                    days = int.from_bytes(days, byteorder='little', signed=False)
                    field_value = datetime.datetime(1, 1, 1) + datetime.timedelta(days=days, seconds=seconds)
                    field_value = str(field_value)

                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_DATETIMEOFFSET.value:

                    field_length = pkt[idx]
                    idx += 1

                    offset_minutes = pkt[idx+field_length-2:idx+field_length]
                    offset_minutes = int.from_bytes(offset_minutes, byteorder='little', signed=True)
                    dt2_bytes = pkt[idx:idx+field_length-2]

                    time_length = field_length - 5
                    time_bytes = dt2_bytes[:time_length]
                    date_bytes = dt2_bytes[time_length:]

                    time_units = int.from_bytes(time_bytes, byteorder='little', signed=False)
                    seconds = time_units / (10 ** fields[i]['scale'])
                    days = int.from_bytes(date_bytes, byteorder='little', signed=False)

                    tzinfo = datetime.timezone(datetime.timedelta(minutes=offset_minutes))
                    delta = datetime.timedelta(days=days, seconds=seconds)

                    field_value = datetime.datetime(1, 1, 1) + delta
                    field_value.replace(tzinfo=tzinfo)
                    field_value = str(field_value)


                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_BIGCHAR.value,
                                           Mssql.FieldType.FIELD_TYPE_NCHAR.value,
                                           Mssql.FieldType.FIELD_TYPE_NVARCHAR.value,
                                           Mssql.FieldType.FIELD_TYPE_BIGVARCHAR.value,
                                          ]:
                    field_length = int.from_bytes(pkt[idx:idx+2], "little")
                    
                    if fields[i]['size'] == 65535:
                        field_value = pkt[idx+12:idx+12+field_length].decode()
                        idx += 12 + 4
                    else:
                        field_value = pkt[idx+2:idx+2+field_length].decode()
                        idx += 2


                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_TEXT.value,
                                           Mssql.FieldType.FIELD_TYPE_NTEXT.value,
                                           Mssql.FieldType.FIELD_TYPE_IMAGE.value
                                          ]:
                    textptr_length = pkt[idx]
                    idx += 1 + textptr_length + 8
                    field_length = int.from_bytes(pkt[idx:idx+4], "little")
                    field_value = pkt[idx+4:idx+4+field_length]

                    if fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_IMAGE.value:
                        field_value = Utils.hex(field_value)
                    else:
                        field_value = field_value.decode()

                    idx += 4

                elif fields[i]['type'] in [Mssql.FieldType.FIELD_TYPE_BIGBINARY.value,
                                           Mssql.FieldType.FIELD_TYPE_BIGVARBIN.value,
                                           ]:
                    if fields[i]['size'] == 65535:
                        field_length = int.from_bytes(pkt[idx:idx+8], "little")
                        chunk_length = int.from_bytes(pkt[idx+8:idx+12], "little")
                        field_value = pkt[idx+12:idx+12+field_length]
                        idx += 12 + 4
                    else:
                        field_length = int.from_bytes(pkt[idx:idx+2], "little")
                        idx += 2
                        field_value = pkt[idx:idx+field_length]

                    field_value = Utils.hex(field_value)

                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_XML.value:
                    plp_length = struct.unpack("<q", pkt[idx:idx+8])
                    field_length = int.from_bytes(pkt[idx+8:idx+12], "little")
                    field_value = pkt[idx+12:idx+12+field_length].decode()
                    idx += 12 + 4

                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_GUID.value:
                    field_length = pkt[idx]
                    tmp = pkt[idx+1:idx+1+field_length]                    
                    field_value = f"{Utils.rev(tmp[0:4]).hex()}-{Utils.rev(tmp[4:6]).hex()}-{Utils.rev(tmp[6:8]).hex()}-{tmp[8:10].hex()}-{tmp[10:].hex()}"

                    idx += 1

                elif fields[i]['type'] == Mssql.FieldType.FIELD_TYPE_SSVARIANT.value:
                    field_length = int.from_bytes(pkt[idx:idx+4], "little")
                    idx += 4 + 8 + 1
                    field_value = pkt[idx:idx+field_length]

                else:
                    field_length = 0
                    field_value = ""

                idx += field_length
                row.append(field_value)


            result.append(row)

        self.result.cols = fields
        self.result.rows = result
        self.result.nb_rows = len(result)


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
        PACKET_TLS = 0x17
        PACKET_UNKNOWN = 0xff
        
