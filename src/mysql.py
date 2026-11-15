import logging
import struct
from enum import Enum

from common import *

logger = logging.getLogger(__name__)

class Mysql:

    def __init__(self):
        self.result = Result()
        self.connection_state = ConnectionState.WAIT_HANDSHAKE

    #@staticmethod
    def replace_query(self, new_query):
        new_query = new_query.encode()
        query_length = len(new_query) + 1
        query_length = query_length.to_bytes(3, 'little')
        return query_length + b"\x00\x16" + new_query


    def parse_header(self, pkt, connection_state):
        payload_length = int.from_bytes(pkt[0:3], "little")
        packet_number = pkt[3]
        payload = pkt[4:]
        self.connection_state = connection_state

        # packet is > 16mb
        if payload_length == 16777215:
            pass

        """
        logger.debug(f"len(pkt) = {len(pkt)}")
        logger.debug(f"len(payload) = {len(payload)}")
        logger.debug(f"payload_length = {payload_length}")
        """
        packet_type = self.get_packet_type(packet_number, payload_length, payload, connection_state)

        return packet_type, payload_length


    def parse_packet(self, pkt, packet_type):
        payload = pkt[4:]

        if packet_type == Mysql.PacketType.PACKET_OK:
            self.parse_OK(payload)

        elif packet_type == Mysql.PacketType.PACKET_ERR:
            self.parse_ERR(payload)

        elif packet_type == Mysql.PacketType.PACKET_PREPARE_STATEMENT:
            query = payload[1:].decode()
            self.result.query = query

        elif packet_type == Mysql.PacketType.PACKET_EXECUTE_STATEMENT:
            self.connection_state = ConnectionState.GOT_PREPARE_STATEMENT
            self.parse_EXECUTE_STATEMENT(payload)

        elif packet_type == Mysql.PacketType.PACKET_QUERY:
            self.connection_state = ConnectionState.GOT_QUERY
            query = payload[1:].decode()
            self.result.query = query

        elif packet_type == Mysql.PacketType.PACKET_HANDSHAKE:
            self.connection_state = ConnectionState.WAIT_HANDSHAKE_RESPONSE
            self.parse_HANDSHAKE(payload)
    
        elif packet_type == Mysql.PacketType.PACKET_HANDSHAKE_RESPONSE:
            self.connection_state = ConnectionState.READY
            self.parse_HANDSHAKE_RESPONSE(payload)

        elif packet_type == Mysql.PacketType.PACKET_TABULAR_RESPONSE:
            self.parse_TABULAR_RESPONSE(payload)

        elif packet_type == Mysql.PacketType.PACKET_USE:
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
        elif packet_number == 3 and payload_length == 1 and payload[0] == 2:
            return Mysql.PacketType.PACKET_REQUEST_PUBLIC_KEY
        elif packet_number == 4 and payload[1:27] == b"-----BEGIN PUBLIC KEY-----":
            return Mysql.PacketType.PACKET_PUBLIC_KEY
        elif packet_number == 5 and payload_length == 256:
            return Mysql.PacketType.PACKET_CACHING_SHA2_RESPONSE
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
            logger.debug(f"parameters {parameters}")

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

        logger.debug(f"db_version {db_version}")

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
        client_capabilities = int.from_bytes(payload[0:2], "little")
        extended_client_capabilities = int.from_bytes(payload[2:4], "little")

        if self.has_capability(client_capabilities, Mysql.Capability.SWITCH_TO_SSL_AFTER_HANDSHAKE):
            logger.debug("Client is SSL ready")

        #23 reserved

        idx = payload.find(0, 32)
        username = payload[32:idx].decode()

        password_length = payload[idx+1]
        idx += 2
        password = payload[idx:idx+password_length]

        idx += password_length
        idx2 = payload.find(0, idx)

        schema = payload[idx:idx2].decode()

        self.result.connection = {'username': username, 'schema': schema, 'password': password.hex()}

    def parse_USE(self, payload):
        logger.debug(f"database: {payload[1:]}")
        self.result.connection = {'database': payload[1:].decode()}

    def parse_SHOW(self, payload):
        logger.debug(f"show: {payload[1:-1]}")



    def parse_TABULAR_RESPONSE(self, payload):

        # Column count (length-encoded integer)
        nb_fields, idx = self.read_lenenc_int(payload, 0)

        # Decode column metadata
        fields, idx = self.parse_field_metadata(payload, idx, nb_fields)
        result = []

        # Decode row packets
        while idx + 4 <= len(payload):

            packet_length = int.from_bytes(payload[idx:idx+3], "little")
            packet_end = idx + 4 + packet_length

            packet_data = payload[idx+4:packet_end]
            idx = packet_end

            if not packet_data:
                continue

            response_code = packet_data[0]

            # EOF packet
            if response_code == 0xfe and packet_length < 9:
                continue

            # Decode row according to protocol

            if self.connection_state == ConnectionState.GOT_QUERY:
                row, _ = self.decode_text_row(packet_data, 0, fields)

            elif self.connection_state == ConnectionState.GOT_PREPARE_STATEMENT:
                if response_code != 0x00:
                    raise ValueError(f"Invalid binary row header: {response_code:#x}")

                row, _ = self.decode_binary_row(packet_data, 0, fields)

            else:
                raise ValueError(f"Unknown row format: {row_format}")

            result.append(row)

        self.result.cols = fields
        self.result.rows = result
        self.result.nb_rows = len(result)


    def decode_binary_value(self, payload, idx, field):
        field_type = field["type"]
        unsigned = bool(field["flags"] & 0x20)

        # Integer types
        integer_types = {
            1: 1,  # TINY
            2: 2,  # SHORT
            3: 4,  # LONG
            8: 8,  # LONGLONG
            9: 4,  # INT24 (4 bytes in binary protocol)
            13: 2, # YEAR
        }

        if field_type in integer_types:
            size = integer_types[field_type]
            value = int.from_bytes(payload[idx:idx + size],"little",signed=False)
            return value, idx + size

        # Floating-point types
        if field_type == 4:  # FLOAT
            return struct.unpack_from("<f", payload, idx)[0], idx + 4

        if field_type == 5:  # DOUBLE
            return struct.unpack_from("<d", payload, idx)[0], idx + 8

        # String, blob, decimal and bit types
        length_encoded_types = {
            15,     # VARCHAR
            16,     # BIT
            246,    # NEWDECIMAL
            249,    # TINY_BLOB
            250,    # MEDIUM_BLOB
            251,    # LONG_BLOB
            252,    # BLOB
            253,    # VAR_STRING
            254,    # STRING
            255,    # GEOMETRY
            247,    # ENUM
            248,    # SET
            245,    # JSON
        }

        if field_type in length_encoded_types:
            value, idx = self.read_lenenc_string(payload, idx)
            return value.decode(), idx

        # Temporal types: length-prefixed binary representation
        temporal_types = {
            7,   # TIMESTAMP
            10,  # DATE
            11,  # TIME
            12,  # DATETIME
        }

        if field_type in temporal_types:
            length = payload[idx]
            idx += 1

            value = payload[idx:idx + length]
            return value, idx + length

        if field_type == 6:  # NULL
            return None, idx

        raise NotImplementedError(
            f"Unsupported MySQL field type: {field_type}"
        )


    def decode_binary_row(self, payload, idx, fields):
        # Skip binary row header (0x00)
        idx += 1

        bitmap_length = (len(fields) + 7 + 2) // 8

        null_bitmap = payload[idx:idx + bitmap_length]
        idx += bitmap_length

        row = []

        for i, field in enumerate(fields):

            # Two reserved bits precede the column bits
            bitmap_pos = i + 2

            if null_bitmap[bitmap_pos // 8] & (1 << (bitmap_pos % 8)):
                row.append(None)
                continue

            value, idx = self.decode_binary_value(
                payload, idx, field
            )

            row.append(value)

        return row, idx



    def decode_text_row(self, payload, idx, fields):
        row = []

        for field in fields:
            value, idx = self.read_lenenc_string(payload, idx)

            if value is None:
                row.append(None)
            else:
                row.append(value.decode("utf-8", errors="replace"))

        return row, idx


    def read_lenenc_int(self, payload, idx):
        first = payload[idx]
        idx += 1

        if first < 0xfb:
            return first, idx

        if first == 0xfb:
            return None, idx

        if first == 0xfc:
            return int.from_bytes(payload[idx:idx+2], "little"), idx + 2

        if first == 0xfd:
            return int.from_bytes(payload[idx:idx+3], "little"), idx + 3

        if first == 0xfe:
            return int.from_bytes(payload[idx:idx+8], "little"), idx + 8

        raise ValueError(f"Invalid length-encoded integer: {first}")


    def read_lenenc_string(self, payload, idx):
        length, idx = self.read_lenenc_int(payload, idx)

        if length is None:
            return None, idx

        value = payload[idx:idx + length]
        return value, idx + length


    def parse_field_metadata(self, payload, idx, nb_fields):
        fields = []

        for _ in range(nb_fields):
            packet_length = int.from_bytes(payload[idx:idx+3], "little")
            idx += 4  # Packet length + sequence number

            names = ["catalog", "database", "table", "original_table", "name", "original_name"]
            field = {}

            for name in names:
                value, idx = self.read_lenenc_string(payload, idx)
                field[name] = value.decode("utf-8", errors="replace") if value else ""

            # Fixed-length metadata section
            fixed_length = payload[idx]
            idx += 1

            if fixed_length < 0x0c:
                raise ValueError("Invalid column metadata section")

            charset = int.from_bytes(payload[idx:idx+2], "little")
            column_length = int.from_bytes(payload[idx+2:idx+6], "little")
            field_type = payload[idx+6]
            flags = int.from_bytes(payload[idx+7:idx+9], "little")
            decimals = payload[idx+9]

            idx += fixed_length

            field["name"] = field["name"] or "(empty string)"
            field["original_name"] = field["original_name"] or "(empty string)"
            field["type"] = field_type
            field["charset"] = charset
            field["length"] = column_length
            field["flags"] = flags
            field["decimals"] = decimals

            fields.append(field)
            #logger.debug(f"Field: {field['name']} type={field_type}")

        return fields, idx


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
        FIELD_TYPE_JSON = 245
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
        PACKET_REQUEST_PUBLIC_KEY = 15
        PACKET_PUBLIC_KEY = 16
        PACKET_CACHING_SHA2_RESPONSE = 17
        PACKET_UNKNOWN = 0xff
