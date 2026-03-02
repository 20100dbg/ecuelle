import struct
from math import ceil
from flags import *
from utils import *

class Packet():

    def __init__(self, pkt, conn_state):
        self.pkt = pkt
        self.conn_state = conn_state
        self.info = {}
        self.debug = True

        try:
            self.parse_packet(pkt)
        except Exception as e:
            print(e)


    def print_debug(self, txt):
        if self.debug:
            print(f"{txt}")


    def parse_packet(self, pkt):

        payload_length = int.from_bytes(pkt[0:3], "little")
        packet_number = pkt[3]
        payload = pkt[4:]

        self.packet_type = self.get_packet_type(packet_number, payload_length, payload)
        #self.print_debug(f"PacketType {packet_type}")

        # packet is > 16mb
        if payload_length == 16777215:
            pass

        if self.packet_type == PacketType.PACKET_OK:
            self.parse_OK(payload)

        elif self.packet_type == PacketType.PACKET_ERR:
            self.parse_ERR(payload)

        elif self.packet_type == PacketType.PACKET_PREPARE_STATEMENT:
            query = payload[1:].decode()
            self.info['query'] = query

        elif self.packet_type == PacketType.PACKET_EXECUTE_STATEMENT:
            self.parse_EXECUTE_STATEMENT(payload)

        elif self.packet_type == PacketType.PACKET_QUERY:
            query = payload[1:]
            self.info['query'] = query

        elif self.packet_type == PacketType.PACKET_HANDSHAKE:
            self.parse_HANDSHAKE(payload)
    
        elif self.packet_type == PacketType.PACKET_HANDSHAKE_RESPONSE:
            self.parse_HANDSHAKE_RESPONSE(payload)

        elif self.packet_type == PacketType.PACKET_TABULAR_RESPONSE:
            self.parse_TABULAR_RESPONSE(payload)


    def get_packet_type(self, packet_number, payload_length, payload):

        if payload[0] == 0 and len(payload) >= 7:
            return PacketType.PACKET_OK
        elif payload[0] == 0xfe and len(payload) < 7:
            return PacketType.PACKET_EOF
        elif payload[0] == 0xff:
            return PacketType.PACKET_ERR
        elif packet_number == 1 and payload_length == 1:
            return PacketType.PACKET_TABULAR_RESPONSE
        elif packet_number == 0 and (payload[0] == 0x0a or payload[0] == 0x09):
            return PacketType.PACKET_HANDSHAKE
        elif packet_number == 1:
            return PacketType.PACKET_HANDSHAKE_RESPONSE
        elif packet_number == 2 and payload_length == 2:
            return PacketType.PACKET_CACHING_SHA2
        elif packet_number == 0 and payload[0] == 0x03:
            return PacketType.PACKET_QUERY
        elif packet_number == 0 and payload[0] == 0x16:
            return PacketType.PACKET_PREPARE_STATEMENT
        elif packet_number == 0 and payload[0] == 0x17:
            return PacketType.PACKET_EXECUTE_STATEMENT
        elif packet_number == 0 and payload[0] == 0x19:
            return PacketType.PACKET_CLOSE
        elif packet_number == 0 and payload[0] == 0x01:
            return PacketType.PACKET_QUIT
        else:
            self.print_debug(f"UNKNOWN PACKET")
            return PacketType.UNKNOWN

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

            self.info['parameters'] = parameters

    def parse_OK(self, payload):
        response_code = payload[0]
        
        if len(payload) == 7:
            self.info['affected_rows'] = payload[1]
            self.info['server_status'] = int.from_bytes(payload[3:4], "little")
            self.info['warnings'] = int.from_bytes(payload[5:6], "little")
        else:
            pass

    def parse_ERR(self, payload):
        self.info['error_code'] = int.from_bytes(payload[1:3], "little")
        self.info['sql_state'] = payload[4:9].decode()
        self.info['error_message'] = payload[9:].decode()

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

            if self.check_capability(self.server_capabilities, Capability.CLIENT_PLUGIN_AUTH.value):
                auth_plugin_data_len = payload[idx+21]
            
            salt_length = max(13, auth_plugin_data_len-8)-1
            salt2 = payload[idx+32:idx+32+salt_length]
            salt = salt1 + salt2
            
            if self.check_capability(self.server_capabilities, Capability.CLIENT_PLUGIN_AUTH.value):
                auth_plugin_name = payload[idx+33+salt_length:-1]


        elif version == 9:
            salt = payload[idx+5:]

        self.info['server_version'] = server_version
        self.info['thread_id'] = thread_id
        self.info['salt'] = salt.hex()


    def parse_HANDSHAKE_RESPONSE(self, payload):
        cap1 = payload[0:2]
        cap2 = payload[2:4]
        self.client_capabilities = int.from_bytes(cap1 + cap2, "little")
        max_packet = int.from_bytes(payload[4:8], "little")
        character_set = payload[8]
        #23 reserved
        idx = payload.find(0, 32)
        username = payload[32:idx]
        password = payload[idx+2:idx+34]
        idx2 = payload.find(0, idx+34)
        schema = payload[idx+34:idx2]
        
        self.info['username'] = username
        self.info['schema'] = schema
        self.info['password'] = Utils.to_hex(password)

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

                    if fields[i]['type'] == FieldType.FIELD_TYPE_TINY.value:
                        field_length = 1
                        row.append(payload[idx])

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_SHORT.value:
                        field_length = 2
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))
                    
                    elif fields[i]['type'] == FieldType.FIELD_TYPE_LONG.value:
                        field_length = 4
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_INT24.value:
                        field_length = 4
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_LONGLONG.value:
                        field_length = 8
                        row.append(int.from_bytes(payload[idx:idx+field_length], "little"))

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_NEWDECIMAL.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length].decode())

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_FLOAT.value:
                        field_length = 4
                        row.append(struct.unpack("<f",payload[idx:idx+field_length])[0])

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_DOUBLE.value:
                        field_length = 8
                        row.append(struct.unpack("<d",payload[idx:idx+field_length])[0])

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_DATE.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        row.append(f"{year}-{month}-{day}")

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_DATETIME.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        hour = payload[idx+4]
                        minute = payload[idx+5]
                        second = payload[idx+6]
                        row.append(f"{year}-{month}-{day} {hour}:{minute}:{second}")

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_TIMESTAMP.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        hour = payload[idx+4]
                        minute = payload[idx+5]
                        second = payload[idx+6]
                        row.append(f"{year}-{month}-{day} {hour}:{minute}:{second}")

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_TIMESTAMP.value:
                        field_length = payload[idx]
                        idx += 1
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        month = payload[idx+2]
                        day = payload[idx+3]
                        hour = payload[idx+4]
                        minute = payload[idx+5]                            
                        second = payload[idx+6]
                        row.append(f"{year}-{month}-{day} {hour}:{minute}:{second}")

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_TIME.value:
                        field_length = payload[idx]
                        idx += 1
                        flags = payload[idx]
                        days = int.from_bytes(payload[idx+1:idx+5], "little")
                        hour = payload[idx+5]
                        minute = payload[idx+6]
                        second = payload[idx+7]
                        row.append(f"{hour}:{minute}:{second}")

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_YEAR.value:
                        field_length = 2
                        year = int.from_bytes(payload[idx:idx+2], "little")
                        row.append(year)

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_VAR_STRING.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length].decode())

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_STRING.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length].decode())

                    elif fields[i]['type'] == FieldType.FIELD_TYPE_BLOB.value:
                        field_length = payload[idx]
                        idx += 1
                        row.append(payload[idx:idx+field_length])

                    #JSON maybe ? who know
                    elif fields[i]['type'] == FieldType.FIELD_TYPE_UNKNOWN.value:
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

        self.info['result'] = result


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
