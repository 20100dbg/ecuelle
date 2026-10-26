import logging
from enum import Enum

from common import *

logger = logging.getLogger(__name__)

class Postgres:

    def __init__(self, pkt, connection_state):
        self.result = Result()
        self.packet_type = None
        self.connection_state = connection_state

        self.parse_header(pkt)
        self.parse_packet(pkt)

    def parse_header(self, pkt):
        self.packet_type = self.get_packet_type(pkt)
        self.payload_length = int.from_bytes(pkt[1:5], "big")

    def get_packet_type(self, pkt):

        if pkt[0] == 0:
            payload_length = int.from_bytes(pkt[0:4], "big")
            payload = pkt[4:]

            if payload_length == 8:
                request_code = int.from_bytes(payload, "big")
                if request_code == 80877103:
                    return Postgres.PacketType.PACKET_SSL_REQUEST

            elif payload_length > 8:
                return Postgres.PacketType.PACKET_STARTUP

        elif len(pkt) == 1 and pkt[0] == 0x4e:
            return Postgres.PacketType.PACKET_SSL_RESPONSE

        elif pkt[0] in [packet_type.value for packet_type in Postgres.PacketType]:
            return Postgres.PacketType(pkt[0])

        return Postgres.PacketType.PACKET_UNKNOWN

    def parse_packet(self, pkt):

        if self.packet_type == Postgres.PacketType.PACKET_QUERY:
            query = pkt[5:-1].decode()

            if query in ["BEGIN", "ROLLBACK", "COMMIT"]:
                query = ""

            self.result.query = query

        elif self.packet_type == Postgres.PacketType.PACKET_ROW_DESCRIPTION:
            self.parse_ROW_DESCRIPTION(pkt)

        elif self.packet_type == Postgres.PacketType.PACKET_ERROR:
            self.parse_ERROR(pkt)

        elif self.packet_type == Postgres.PacketType.PACKET_STARTUP:
            self.parse_STARTUP(pkt)

        elif self.packet_type == Postgres.PacketType.PACKET_AUTH_REQUEST:
            self.parse_AUTH_REQUEST(pkt)


    def parse_STARTUP(self, pkt):
        payload_length = int.from_bytes(pkt[0:4], "big")

        username = schema = ''

        idx = 8
        while idx < payload_length - 1:
            idx_end = pkt.find(0, idx)
            parameter_name = pkt[idx:idx_end].decode()

            idx = idx_end + 1
            idx_end = pkt.find(0, idx)
            parameter_value = pkt[idx:idx_end].decode()
            idx = idx_end + 1

            if parameter_name == 'user':
                username = parameter_value
            elif parameter_name == 'database':
                schema = parameter_value

        self.result.connection = {'username': username, 'schema': schema}


    def parse_AUTH_REQUEST(self, pkt):
        auth_type = int.from_bytes(pkt[5:9], "big")

        if auth_type == 12:
            idx = 0
            while idx < len(pkt):
                type = pkt[idx]
                idx += 1
                payload_length = int.from_bytes(pkt[idx:idx+4], "big")

                if type == 0x53: #Parameter status

                    idx_start = idx + 4
                    idx_end = pkt.find(0, idx_start)
                    parameter_name = pkt[idx_start:idx_end].decode()

                    idx_start = idx_end + 1
                    idx_end = pkt.find(0, idx_start)
                    parameter_value = pkt[idx_start:idx_end].decode()
                    idx_start = idx_end + 1

                    if parameter_name == "server_version":
                        db_version = parameter_value.split()[0]
                        self.result.connection = {'db_version': db_version}

                idx = idx + payload_length



    def parse_ERROR(self, pkt):
        idx = 5
        idx_end = pkt.find(0, idx)
        #severity = pkt[idx+1:idx_end]

        idx = idx_end + 1
        idx_end = pkt.find(0, idx)
        #text = pkt[idx+1:idx_end]

        idx = idx_end + 1
        idx_end = pkt.find(0, idx+1)
        code = pkt[idx:idx_end].decode()

        idx = idx_end + 1
        idx_end = pkt.find(0, idx+1)
        message = pkt[idx+1:idx_end].decode()

        #logger.debug(f"severity {severity}, text {text}, code {code}, message {message}")
        self.result.error = {'code': code, 'state': '', 'message': message}


    def parse_ROW_DESCRIPTION(self, pkt):
        field_count = int.from_bytes(pkt[5:7], "big")
        idx = 7
        field_names = []
        rows = []

        for _ in range(field_count):
            idx2 = pkt.find(0, idx)
            column_name = pkt[idx:idx2].decode()
            oid_type = pkt[idx2+7:idx2+11]

            field_names.append({'name': column_name, 'type': oid_type})
            idx = idx2 + 19


        while pkt[idx] == Postgres.PacketType.PACKET_DATA_ROW.value:
            #payload_length = int.from_bytes(pkt[idx+1:idx+5], "big")
            field_count = int.from_bytes(pkt[idx+5:idx+7], "big")
            idx += 7

            row = []

            for _ in range(field_count):
                column_length = int.from_bytes(pkt[idx:idx+4], "big")
                if column_length == 4294967295:
                    column_length = -1

                if column_length > 0:
                    data = pkt[idx+4:idx+4+column_length].decode()
                else:
                    data = ""

                row.append(data)
                idx += 4 + column_length

            rows.append(row)

        self.result.cols = field_names
        self.result.rows = rows
        self.result.nb_rows = len(rows)


    class PacketType(Enum):
        PACKET_SSL_REQUEST = 0x00
        PACKET_SSL_RESPONSE = 0x01
        PACKET_STARTUP = 0x02
        PACKET_COMPLETION = 0x43
        PACKET_DATA_ROW = 0x44
        PACKET_ERROR = 0x45
        PACKET_QUERY = 0x51
        PACKET_AUTH_REQUEST = 0x52
        PACKET_ROW_DESCRIPTION = 0x54
        PACKET_TERMINATION = 0x58
        PACKET_READY_FOR_QUERY = 0x5a
        PACKET_SASL_RESPONSE = 0x70
        PACKET_UNKNOWN = 0xff
