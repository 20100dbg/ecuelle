import logging
from enum import Enum

from common import *

logger = logging.getLogger(__name__)

class Mysql:

    def __init__(self, pkt, connection_state):
        self.result = Result()
        self.packet_type = None
        self.connection_state = connection_state

        self.parse_header(pkt, connection_state)
        self.parse_packet(self.payload)


    #@staticmethod
    def replace_query(self, new_query):
        new_query = new_query.encode()
        query_length = len(new_query) + 1
        query_length = query_length.to_bytes(3, 'little')
        return query_length + b"\x00\x16" + new_query


    def parse_header(self, pkt, connection_state):
        self.payload_length = int.from_bytes(pkt[0:3], "little")
        self.packet_number = pkt[3]
        self.payload = pkt[4:]

        if len(self.payload) != self.payload_length:
            logger.debug(f"len(self.payload) = {len(self.payload)}")
            logger.debug(f"self.payload_length = {self.payload_length}")
            #raise ValueError("Invalid payload length")

        self.packet_type = self.get_packet_type(self.packet_number, self.payload_length, self.payload, connection_state)

    def parse_packet(self, payload):

        # packet is > 16mb
        if self.payload_length == 16777215:
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
            self.connection_state = ConnectionState.WAIT_HANDSHAKE_RESPONSE
            self.parse_HANDSHAKE(payload)
    
        elif self.packet_type == Mysql.PacketType.PACKET_HANDSHAKE_RESPONSE:
            self.connection_state = ConnectionState.READY
            self.parse_HANDSHAKE_RESPONSE(payload)

        elif self.packet_type == Mysql.PacketType.PACKET_TABULAR_RESPONSE:
            self.parse_TABULAR_RESPONSE(payload)

        elif self.packet_type == Mysql.PacketType.PACKET_USE:
            self.parse_USE(payload)


    def get_packet_type(self, packet_number, payload_length, payload, connection_state):

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
        elif packet_number == 1 and connection_state == ConnectionState.WAIT_HANDSHAKE_RESPONSE:
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
        elif packet_number == 0 and payload[0] == 0x02:
            return Mysql.PacketType.PACKET_USE
        elif packet_number == 0 and payload[0] == 0x04:
            return Mysql.PacketType.PACKET_SHOW
        else:
            return Mysql.PacketType.PACKET_UNKNOWN

    def parse_EXECUTE_STATEMENT(self, payload):
        
        #if there is parameters
        if len(payload) > 10:
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
        #response_code = payload[0]
        
        if len(payload) == 7:
            self.result.nb_rows = payload[1]
            #server_status = int.from_bytes(payload[3:4], "little")
            #warnings = int.from_bytes(payload[5:6], "little")


    def parse_ERR(self, payload):
        code = int.from_bytes(payload[1:3], "little")
        state = payload[4:9].decode()
        message = payload[9:].decode()

        #self.result.error = message
        self.result.error = {'code': code, 'state': state, 'message': message}

    def parse_HANDSHAKE(self, payload):
        version = payload[0]

        idx = payload.find(0)
        db_version = payload[1:idx].decode()

        if version == 10:
            salt1 = payload[idx+5:idx+13]
            server_capabilities = int.from_bytes(payload[idx+14:idx+16], "little")
            extended_server_capabilities = int.from_bytes(payload[idx+19:idx+21], "little")
            auth_plugin_data_len = 0

            if self.has_capability(server_capabilities, Mysql.Capability.SWITCH_TO_SSL_AFTER_HANDSHAKE):
                logger.debug("Server is SSL ready")

            salt_length = max(13, auth_plugin_data_len-8)-1
            salt2 = payload[idx+32:idx+32+salt_length]
            salt = salt1 + salt2
            

        elif version == 9:
            salt = payload[idx+5:]

        self.result.connection = {'db_version': db_version, 'salt': salt.hex()}


    def parse_HANDSHAKE_RESPONSE(self, payload):
        logger.debug("inside parse_HANDSHAKE_RESPONSE")

        client_capabilities = int.from_bytes(payload[0:2], "little")
        extended_client_capabilities = int.from_bytes(payload[2:4], "little")

        if self.has_capability(client_capabilities, Mysql.Capability.SWITCH_TO_SSL_AFTER_HANDSHAKE):
            logger.debug("Client is SSL ready")

        #23 reserved

        idx = payload.find(0, 32)
        username = payload[32:idx].decode()
        logger.debug(f"username: {username}")

        password_length = payload[idx+1]
        idx += 2
        password = payload[idx:idx+password_length]
        logger.debug(f"password: {password.hex()}")

        idx += password_length
        idx2 = payload.find(0, idx)

        schema = payload[idx:idx2].decode()
        logger.debug(f"schema: {schema}")

        self.result.connection = {'username': username, 'schema': schema, 'password': password.hex()}

    def parse_USE(self, payload):
        logger.debug(f"database: {payload[1:]}")
        self.result.connection = {'database': payload[1:].decode()}

    def parse_SHOW(self, payload):
        logger.debug(f"show: {payload[1:-1]}")

    def parse_TABULAR_RESPONSE(self, payload):
        
        # Column count
        nb_fields = payload[0]
        idx = 1
        result = []
        fields = []

        # Field packet
        for _ in range(nb_fields):

            packet_length = int.from_bytes(payload[idx:idx+3], "little")
            #packet_number = payload[idx + 3]

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

            #charset = payload[idx+1]
            field_length = int.from_bytes(payload[idx+3:idx+7], "little")
            field_type = payload[idx+7]

            if not field_name: field_name = "(empty string)"
            if not field_original_name: field_original_name = "(empty string)"

            logger.debug(f"field: {field_name} {field_type}")
            fields.append({'name': field_name, 'original_name': field_original_name, 'type': field_type})

            #skip 00 00
            idx += 11 + 2

        #End field packets

        #row packets
        got_intermediate_eof = False

        while True:

            row = []

            packet_length = int.from_bytes(payload[idx:idx+3], "little")
            #packet_number = payload[idx+3]
            response_code = payload[idx+4]
            idx += 4

            if packet_length < 8 and response_code == 0xfe:
                if not got_intermediate_eof and (idx + packet_length) < len(payload):
                    got_intermediate_eof = True
                    idx += 5
                    continue
                else:
                    break

            else:

                if packet_length == 1:
                    row.append("")
                    idx += 1

                else:
                    for i in range(len(fields)):
                        field_length = payload[idx]

                        if field_length == 0xfb:
                            val = "NULL"
                            field_length = 0

                        elif field_length > 0:
                            val = payload[idx+1:idx+1+field_length]
                            val = val.decode()

                        else:
                            val = "(empty string)"


                        logger.debug(f"field {fields[i]['name']} = {val}")
                        row.append(val)
                        idx += 1 + field_length

                    result.append(row)

        self.result.cols = fields
        self.result.rows = result
        self.result.nb_rows = len(result)


    def has_capability(self, capabilities, cap):
        return (capabilities & cap.value) == cap.value


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
        LONG_PASSWORD = 1
        FOUND_ROWS = 1 << 1
        LONG_COLUMNS_FLAG = 1 << 2
        CONNECT_WITH_DATABASE = 1 << 3
        DONT_ALLOW_DATABASE_TABLE_COLUMN =  1 << 4
        CAN_USE_COMPRESSION_PROTOCOL = 1 << 5
        ODBC_CLIENT = 1 << 6
        CAN_USE_LOAD_DATA_LOCAL = 1 << 7
        IGNORE_SPACES_BEFORE_PARENTHESIS = 1 << 8
        SPEAKS_4_1_PROTOCOL = 1 << 9
        INTERACTIVE_CLIENT = 1 << 10
        SWITCH_TO_SSL_AFTER_HANDSHAKE = 1 << 11
        IGNORE_SIGPIPES = 1 << 12
        KNOWS_ABOUT_TRANSACTIONS = 1 << 13
        SPEAKS_4_1_PROTOCOL_OLD_FLAG = 1 << 14
        CAN_DO_4_1_AUTHENTICATION =  1 << 15
        
    class ExtendedCapability(Enum):
        MULTIPLE_STATEMENTS = 1
        MULTIPLE_RESULTS = 1 << 1
        PS_MULTIPLE_RESULTS = 1 << 2
        PLUGIN_AUTH = 1 << 3
        CONNECT_ATTRS = 1 << 4
        PLUGIN_AUTH_LENENC_CLIENT_DATA = 1 << 5
        CLIENT_CAN_HANDLE_EXPIRED_PASSWORDS = 1 << 6
        SESSION_VARIABLE_TRACKING = 1 << 7
        DEPRECATE_EOF = 1 << 8
        CLIENT_CAN_HANDLE_OPTIONAL_RESULTSET_METADATA = 1 << 9
        ZSTD_COMPRESSION_ALGORITHM = 1 << 10
        QUERY_ATTRIBUTES = 1 << 11
        MULTIFACTOR_AUTHENTICATION = 1 << 12
        CAPABILITY_EXTENSION = 1 << 13
        CLIENT_VERIFIES_SERVER_TLS_CERTIFICATES = 1 << 14
        UNUSED = 1 << 15

    class FieldType(Enum):
        FIELD_TYPE_TINY = 1
        FIELD_TYPE_SHORT = 2
        FIELD_TYPE_LONG = 3
        FIELD_TYPE_FLOAT = 4
        FIELD_TYPE_DOUBLE = 5
        FIELD_TYPE_NULL = 6
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
        PACKET_USE = 13
        PACKET_SHOW = 14
        PACKET_UNKNOWN = 0xff
