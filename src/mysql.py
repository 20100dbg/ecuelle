import struct
from math import ceil
from common import *
from enum import Enum


class Mysql():

    def __init__(self, pkt):
        self.pkt = pkt
        self.result = Result()
        self.debug = True
        self.packet_type = None

        try:
            self.parse_packet(pkt)
        except Exception as e:
            print(e)

    #@staticmethod
    def replace_query(self, new_query):
        new_query = new_query.encode()
        query_length = len(new_query) + 1
        query_length = query_length.to_bytes(3, 'little')
        return query_length + b"\x00\x16" + new_query

    def print_debug(self, txt):
        if self.debug:
            print(f"{txt}")


    def parse_packet(self, pkt):

        payload_length = int.from_bytes(pkt[0:3], "little")
        packet_number = pkt[3]
        payload = pkt[4:]

        self.packet_type = self.get_packet_type(packet_number, payload_length, payload)
        #self.print_debug(f"Mysql.PacketType {packet_type}")

        # packet is > 16mb
        if payload_length == 16777215:
            pass

        if self.packet_type == Mysql.PacketType.PACKET_OK:
            self.parse_OK(payload)

        elif self.packet_type == Mysql.PacketType.PACKET_ERR:
            self.parse_ERR(payload)

        elif self.packet_type == Mysql.PacketType.PACKET_PREPARE_STATEMENT:
            query = payload[1:].decode()
            self.result.query = query

        elif self.packet_type == Mysql.PacketType.PACKET_EXECUTE_STATEMENT:
            self.parse_EXECUTE_STATEMENT(payload)

        elif self.packet_type == Mysql.PacketType.PACKET_QUERY:
            query = payload[1:].decode()
            self.result.query = query

        elif self.packet_type == Mysql.PacketType.PACKET_HANDSHAKE:
            self.parse_HANDSHAKE(payload)
    
        elif self.packet_type == Mysql.PacketType.PACKET_HANDSHAKE_RESPONSE:
            self.parse_HANDSHAKE_RESPONSE(payload)

        elif self.packet_type == Mysql.PacketType.PACKET_TABULAR_RESPONSE:
            self.parse_TABULAR_RESPONSE(payload)


    def get_packet_type(self, packet_number, payload_length, payload):

        if payload[0] == 0 and len(payload) >= 7:
            return Mysql.PacketType.PACKET_OK
        elif payload[0] == 0xfe and len(payload) < 7:
            return Mysql.PacketType.PACKET_EOF
        elif payload[0] == 0xff:
            return Mysql.PacketType.PACKET_ERR
        elif packet_number == 1 and payload_length == 1:
            return Mysql.PacketType.PACKET_TABULAR_RESPONSE
        elif packet_number == 0 and (payload[0] == 0x0a or payload[0] == 0x09):
            return Mysql.PacketType.PACKET_HANDSHAKE
        elif packet_number == 1:
            return Mysql.PacketType.PACKET_HANDSHAKE_RESPONSE
        elif packet_number == 2 and payload_length == 2:
            return Mysql.PacketType.PACKET_CACHING_SHA2
        elif packet_number == 0 and payload[0] == 0x03:
            return Mysql.PacketType.PACKET_QUERY
        elif packet_number == 0 and payload[0] == 0x16:
            return Mysql.PacketType.PACKET_PREPARE_STATEMENT
        elif packet_number == 0 and payload[0] == 0x17:
            return Mysql.PacketType.PACKET_EXECUTE_STATEMENT
        elif packet_number == 0 and payload[0] == 0x19:
            return Mysql.PacketType.PACKET_CLOSE
        elif packet_number == 0 and payload[0] == 0x01:
            return Mysql.PacketType.PACKET_QUIT
        else:
            return Mysql.PacketType.PACKET_UNKNOWN

    def parse_EXECUTE_STATEMENT(self, payload):
        
        statement_id = int.from_bytes(payload[1:5], "little")
        flags = payload[5]
        iterations = int.from_bytes(payload[6:10], "little")
        
        #if there is parameters
        if len(payload) > 10:
            bound_flag = payload[11]
            idx = 12

            nb_parameters = 0
            parameters = []

            while True:
                if payload[idx] == 0xfd and payload[idx+1] == 0x00:
                    nb_parameters += 1
                else:
                    break
                idx += 2

            for _ in range(nb_parameters):
                parameter_length = payload[idx]
                parameter = payload[idx+1:idx+1+parameter_length].decode()
                parameters.append(parameter)
                idx += 1 + parameter_length

            self.result.parameters = parameters

    def parse_OK(self, payload):
        response_code = payload[0]
        
        if len(payload) == 7:
            self.result.nb_rows = payload[1]
            server_status = int.from_bytes(payload[3:4], "little")
            warnings = int.from_bytes(payload[5:6], "little")

            self.result.info = {'server_status': server_status, 'warnings': warnings}


    def parse_ERR(self, payload):
        error_code = int.from_bytes(payload[1:3], "little")
        sql_state = payload[4:9].decode()
        error_message = payload[9:].decode()

        #self.result.error = {'error_code': error_code, 'sql_state': sql_state, 'error_message': error_message}
        self.result.error = error_message

    def parse_HANDSHAKE(self, payload):
        version = payload[0]

        idx = payload.find(0)
        server_version = payload[1:idx]
        thread_id = int.from_bytes(payload[idx+1:idx+5], "little")

        if version == 10:
            salt1 = payload[idx+5:idx+13]
            cap1 = payload[idx+14:idx+16]
            character_set = payload[idx+16]
            status_flags = payload[idx+17:idx+19]
            cap2 = payload[idx+19:idx+21]
            auth_plugin_data_len = 0
            auth_plugin_name = ""
            self.server_capabilities = int.from_bytes(cap1+cap2, "little")

            if self.check_capability(self.server_capabilities, Mysql.Capability.CLIENT_PLUGIN_AUTH.value):
                auth_plugin_data_len = payload[idx+21]
            
            salt_length = max(13, auth_plugin_data_len-8)-1
            salt2 = payload[idx+32:idx+32+salt_length]
            salt = salt1 + salt2
            
            if self.check_capability(self.server_capabilities, Mysql.Capability.CLIENT_PLUGIN_AUTH.value):
                auth_plugin_name = payload[idx+33+salt_length:-1]


        elif version == 9:
            salt = payload[idx+5:]

        self.result.info = {'server_version': server_version, 'salt': salt.hex()}


    def parse_HANDSHAKE_RESPONSE(self, payload):
        cap1 = payload[0:2]
        cap2 = payload[2:4]
        self.client_capabilities = int.from_bytes(cap1 + cap2, "little")
        max_packet = int.from_bytes(payload[4:8], "little")
        character_set = payload[8]
        #23 reserved
        idx = payload.find(0, 32)
        username = payload[32:idx].decode()
        password = payload[idx+2:idx+34]
        idx2 = payload.find(0, idx+34)
        schema = payload[idx+34:idx2].decode()
        
        self.result.info = {'username': username, 'schema': schema, 'password': password.hex()}

    def parse_TABULAR_RESPONSE(self, payload):
        
        # Column count
        nb_fields = payload[0]
        idx = 1
        result = []
        fields = []


        # Field packet
        for _ in range(nb_fields):

            packet_length = int.from_bytes(payload[idx:idx+3], "little")
            #self.print_debug(f"packet_length : {packet_length}")
            packet_number = payload[idx + 3]
            #self.print_debug(f"packet_number : {packet_number}")

            idx += 4
            fields_name = ['catalog', 'database', 'table', 'original_table', 'name', 'original_name']
            field_name = field_original_name = ''

            for fn in fields_name:
                field_length = payload[idx]
                field_value = payload[idx+1:idx+1+field_length]
                
                if fn == 'name':
                    field_name = field_value.decode()

                elif fn == 'original_name':
                    field_original_name = field_value.decode()

                idx += 1+field_length
                #self.print_debug(f"field {fn} : {field_value}")

            charset = payload[idx+1]
            field_length = int.from_bytes(payload[idx+3:idx+7], "little")
            field_type = payload[idx+7]

            flags = payload[idx+8:idx+10] # int.from_bytes(payload[idx:idx+2], "little")
            decimals = payload[idx+10]

            fields.append({'name': field_name, 'original_name': field_original_name, 'type': field_type})

            #skip 00 00
            idx += 11 + 2

        #End field packets


        #row packets
        got_intermediate_eof = False

        while True:

            row = []

            packet_length = int.from_bytes(payload[idx:idx+3], "little")
            packet_number = payload[idx+3]
            response_code = payload[idx+4]
            idx += 4

            if packet_length == 5 and response_code == 0xfe:
                if not got_intermediate_eof:
                    got_intermediate_eof = True
                    idx += 5
                    continue
                else:
                    break

            elif response_code == 0x00:
                idx += 1
                idx_field = 0
                row_null_buffer_len = 1

                #first row_null_buffer byte
                for x in [4,8,16,32,64,128]:                    
                    fields[idx_field]['is_null'] = payload[idx] & x == x

                    idx_field += 1
                    if idx_field >= len(fields):
                        break

                idx += 1

                if nb_fields > 6:
                    row_null_buffer_len = ceil((nb_fields-6) / 8)

                    for y in range(row_null_buffer_len):
                        for x in [1,2,4,8,16,32,64,128]:                        
                            fields[idx_field]['is_null'] = payload[idx+y] & x == x
                            
                            idx_field += 1
                            if idx_field >= len(fields):
                                break

                    idx += row_null_buffer_len


                for i in range(len(fields)):

                    if fields[i]['is_null']:
                        row.append(None)
                        continue

                    if fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_TINY.value:
                        field_length = 1
                        row.append(payload[idx])

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_SHORT.value:
                        field_length = 2
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))
                    
                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_LONG.value:
                        field_length = 4
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_INT24.value:
                        field_length = 4
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_LONGLONG.value:
                        field_length = 8
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_NEWDECIMAL.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length].decode())

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_FLOAT.value:
                        field_length = 4
                        row.append(struct.unpack("<f",payload[idx:idx+field_length])[0])

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_DOUBLE.value:
                        field_length = 8
                        row.append(struct.unpack("<d",payload[idx:idx+field_length])[0])

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_DATE.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        row.append(f"{year}-{month}-{day}")

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_DATETIME.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        hour = payload[idx+4]
                        minute = payload[idx+5]
                        second = payload[idx+6]
                        row.append(f"{year}-{month}-{day} {hour}:{minute}:{second}")

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_TIMESTAMP.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        hour = payload[idx+4]
                        minute = payload[idx+5]
                        second = payload[idx+6]
                        row.append(f"{year}-{month}-{day} {hour}:{minute}:{second}")

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_TIMESTAMP.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        hour = payload[idx+4]
                        minute = payload[idx+5]                            
                        second = payload[idx+6]
                        row.append(f"{year}-{month}-{day} {hour}:{minute}:{second}")

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_TIME.value:
                        field_length = payload[idx]
                        idx += 1
                        flags = payload[idx]
                        days = int.from_bytes(payload[idx+1:idx+5], "little")
                        hour = payload[idx+5]
                        minute = payload[idx+6]
                        second = payload[idx+7]
                        row.append(f"{hour}:{minute}:{second}")

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_YEAR.value:
                        field_length = 2
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        row.append(year)

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_VAR_STRING.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length].decode())

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_STRING.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length].decode())

                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_BLOB.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length])

                    #JSON maybe ? who know
                    elif fields[i]['type'] == Mysql.FieldType.FIELD_TYPE_UNKNOWN.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length])

                    else:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length])

                    #print(f"{fields[i]['name']} - {row[-1]} {payload[idx:idx+field_length]}")
                    idx += field_length

                result.append(row)

            #Query
            else:

                for i in range(len(fields)):
                    field_length = payload[idx]
                    row.append(payload[idx+1:idx+1+field_length].decode())                    
                    idx += 1 + field_length

                result.append(row)

        self.result.rows = result
        self.result.nb_rows = len(result)


    def check_capability(self, capabilities, val):
        return (capabilities & val) == val


    def read_length_encoded_integer(self, x):
        if len(x) == 1:
            return x
        elif x[0] == 0xfc:
            return int.from_bytes(payload[1:2], "little")
        elif x[0] == 0xfd:
            return int.from_bytes(payload[1:3], "little")
        elif x[0] == 0xfe:
            return int.from_bytes(payload[1:8], "little")

    
    class Capability(Enum):
        CLIENT_LONG_PASSWORD = 1
        CLIENT_FOUND_ROWS = 2
        CLIENT_LONG_FLAG = 1 << 2
        CLIENT_CONNECT_WITH_DB = 1 << 3
        CLIENT_NO_SCHEMA =  1 << 4
        CLIENT_COMPRESS = 1 << 5
        CLIENT_ODBC = 1 << 6
        CLIENT_LOCAL_FILES = 1 << 7
        CLIENT_IGNORE_SPACE = 1 << 8
        CLIENT_PROTOCOL_41 = 1 << 9
        CLIENT_INTERACTIVE = 1 << 10
        CLIENT_SSL = 1 << 11
        CLIENT_IGNORE_SIGPIPE = 1 << 12
        CLIENT_TRANSACTIONS = 1 << 13
        CLIENT_RESERVED = 1 << 14
        CLIENT_RESERVED2 =  1 << 15
        CLIENT_MULTI_STATEMENTS = 1 << 16
        CLIENT_MULTI_RESULTS = 1 << 17
        CLIENT_PS_MULTI_RESULTS = 1 << 18
        CLIENT_PLUGIN_AUTH = 1 << 19
        CLIENT_CONNECT_ATTRS = 1 << 20
        CLIENT_PLUGIN_AUTH_LENENC_CLIENT_DATA = 1 << 21
        CLIENT_CAN_HANDLE_EXPIRED_PASSWORDS = 1 << 22
        CLIENT_SESSION_TRACK = 1 << 23
        CLIENT_DEPRECATE_EOF = 1 << 24
        CLIENT_OPTIONAL_RESULTSET_METADATA = 1 << 25
        CLIENT_ZSTD_COMPRESSION_ALGORITHM = 1 << 26
        CLIENT_QUERY_ATTRIBUTES = 1 << 27
        MULTI_FACTOR_AUTHENTICATION = 1 << 28
        CLIENT_CAPABILITY_EXTENSION = 1 << 29
        CLIENT_SSL_VERIFY_SERVER_CERT = 1 << 30
        CLIENT_REMEMBER_OPTIONS = 1 << 31

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
        PACKET_OK = 1
        PACKET_EOF = 2
        PACKET_ERR = 3
        PACKET_HANDSHAKE = 4
        PACKET_HANDSHAKE_RESPONSE = 5
        PACKET_CACHING_SHA2 = 6
        PACKET_QUERY = 7
        PACKET_PREPARE_STATEMENT = 8
        PACKET_EXECUTE_STATEMENT = 9
        PACKET_TABULAR_RESPONSE = 10
        PACKET_CLOSE = 11
        PACKET_QUIT = 12
        PACKET_UNKNOWN = 0xff
