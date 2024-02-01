from adafruit_itertools import cycle
from binascii import crc32, hexlify
import struct


# define xor encryption
def xor_crypt(a: str, b: str):
    return "".join(chr(ord(x) ^ ord(y)) for x, y in zip(a, cycle(b)))


# unpack data from udp receives
def unpack_data(pack_data: bytes, size: int, secret: str):
    """数据解码"""
    if size != 0:
        msgtype = pack_data[0]
        datalen = pack_data[1]
        crc_bytes = struct.unpack("4B", pack_data[4:8])
        reversed_crc_bytes = bytearray()
        for i in range(len(crc_bytes) - 1, -1, -1):
            reversed_crc_bytes.append(crc_bytes[i])
        crc1 = hexlify(reversed_crc_bytes).decode()
        crc2 = "{:08x}".format(crc32(pack_data[8 : datalen + 8]))
        realdata = bytearray(pack_data[8 : datalen + 8])
        realdata = bytes(xor_crypt(realdata.decode("ascii"), secret), "ascii")
        return msgtype, datalen, realdata, crc1, crc2
    return 0, 0, b"", "", ""


# prepare data for udp sends
def pack_data(msgtype: int, message: str, secret: str):
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
