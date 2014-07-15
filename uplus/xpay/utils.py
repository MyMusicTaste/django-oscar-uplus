# -*- coding: utf-8 -*-
import md5
from uplus.xpay import config_uplus

def _hex_encode(tobe_encoded):
    hex_values = []
    for each_chr in tobe_encoded:
        hex_value = hex(ord(each_chr))[2:]
        if len(hex_value) == 1:
            hex_value = "0" + hex_value
        hex_values.append(hex_value)

    encoded_value = "".join(hex_values)
    return encoded_value

def _create_hash(oid, total, timestamp=None, code=None):
    m=md5.new()
    m.update(config_uplus.LGUPLUS_MID)
    m.update(str(oid))
    m.update(str(total))
    if code is not None:
        m.update(code)
    if timestamp is not None:
        m.update(timestamp)
    m.update(config_uplus.LGUPLUS_SECRET_MERTKEY)
    return _hex_encode(m.digest())

def _get_receipt_hash(tid):
    m=md5.new()
    m.update(config_uplus.LGUPLUS_MID)
    m.update(str(tid))
    m.update(config_uplus.LGUPLUS_SECRET_MERTKEY)
    return _hex_encode(m.digest())

