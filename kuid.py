#!/usr/bin/python

"""
推断 Klei User ID 到玩家存档路径的编码形式
"""

import base64


def decode(s: str, order_str: str) -> bytes:
    pad_n = 8 - len(s) % 8
    trans_dict = str.maketrans(order_str, "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567")
    result = base64.b32decode(s.translate(trans_dict) + "=" * pad_n)
    return result


kuid = "KU_WRv6AVc8"
# KU_ 应该是固定前缀
# 后跟的 WRv6AVc8 应该是实际 ID
# 会出现 63 种字符 A-Z a-z 0-9 _
# ？？？？为啥会少一位呢
# 像是自定义的 base64，可能背后是 6 个字节的数据


path = "A7K1NP32JUC8"
# 总是以 A7 打头
# 后面会出现 32 种字符 A-V 0-9
# 应该是自定义的 base32
# 但是 base32 编码后的字符串长度应该是可以整除 8
# 用 base32 的方式解需要在后面补 "="，补后解码获得的是 7 个字节

print(f"{kuid=}")
print(f"{path=}")

print(base64.b64decode("WRv6AVc8").hex())
print(int.from_bytes(base64.b64decode("WRv6AVc8")))
print(int.from_bytes(base64.b64decode("WRv6AVc8"), "little"))
order_str_list = [
    "ABCDEFGHIJKLMNOPQRSTUV0123456789",
    "ABCDEFGHIJKLMNOPQRSTUV1234567890",
    "0123456789ABCDEFGHIJKLMNOPQRSTUV",
    "1234567890ABCDEFGHIJKLMNOPQRSTUV",
]
for order_str in order_str_list:
    b = decode(path, order_str)
    print(f"{b.hex()=}\t{int.from_bytes(b)=}\t{int.from_bytes(b,'little')=}")
