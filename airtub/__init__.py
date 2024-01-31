from adafruit_itertools import cycle
from binascii import crc32

# define xor encryption
def xor_crypt(a: str, b: str):
    return "".join(chr(ord(x) ^ ord(y)) for x, y in zip(a, cycle(b)))


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
