""" provide functions for data packing and unpacking """

import struct
from binascii import crc32, hexlify
from adafruit_itertools import cycle


def xor_crypt(a: str, b: str):
    """define xor encryption"""
    return "".join(chr(ord(x) ^ ord(y)) for x, y in zip(a, cycle(b)))


def unpack_data(raw_data: bytes, size: int, secret: str):
    """unpack data from udp receives"""
    if size != 0:
        msgtype = raw_data[0]
        datalen = raw_data[1]
        crc_bytes = struct.unpack("4B", raw_data[4:8])
        reversed_crc_bytes = bytearray()
        for i in range(len(crc_bytes) - 1, -1, -1):
            reversed_crc_bytes.append(crc_bytes[i])
        crc1 = hexlify(reversed_crc_bytes).decode()
        crc2 = "{:08x}".format(crc32(raw_data[8 : datalen + 8]))
        realdata = bytearray(raw_data[8 : datalen + 8])
        realdata = bytes(xor_crypt(realdata.decode("ascii"), secret), "ascii")
        return msgtype, datalen, realdata, crc1, crc2
    return 0, 0, b"", "", ""


def pack_data(msgtype: int, message: str, secret: str):
    """prepare data for udp sends"""
    len_num = len(message)
    crypt_data = xor_crypt(message, secret).encode("ascii")
    crc = crc32(crypt_data).to_bytes(4, "little")

    send_data = bytearray()
    send_data.extend(bytearray([msgtype, len_num, 0, 0]))
    send_data.extend(crc)
    send_data.extend(crypt_data)

    empty_len = 188 - 8 - len_num
    empty_array = bytearray(empty_len)
    send_data.extend(empty_array)

    return bytes(send_data)
