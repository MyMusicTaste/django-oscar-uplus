# -*- coding: utf-8 -*-
__author__ = 'nujabes8'

from django.conf import settings
LGUPLUS_TEST = settings.DEBUG

server_id = 01
timeout = 60
log_level = 4
verify_cert = 0
verify_host = 0
report_error = 1
output_UTF8 = 1
auto_rollback = 1
log_dir ='/home/ubuntu'
output_UTF8 = 1

LGUPLUS_MID = 'tX_jjsmedia' if LGUPLUS_TEST else 'X_jjsmedia'
LGUPLUS_SECRET_MERTKEY = 'a7daafe1257dcae2396f7d281de75d2c' if LGUPLUS_TEST else 'a7daafe1257dcae2396f7d281de75d2c'

dacom_url = 'https://xpayclient.lgdacom.net/xpay/Gateway.do'
test_url = 'https://xpayclient.lgdacom.net:7443/xpay/Gateway.do'
aux_url = 'http://xpayclient.lgdacom.net:7080/xpay/Gateway.do'

if LGUPLUS_TEST:
    UPLUS_RETURN_URL = "http://hanilove.co.kr/payment/uplus/return"
    UPLUS_ISPWAP_URL = "http://hanilove.co.kr/payment/uplus/isp/return"
    UPLUS_ISPCANCEL_URL = "http://hanilove.co.kr/payment/uplus/isp/cancel"
    UPLUS_ISPNOTE_URL = "http://hanilove.co.kr/payment/uplus/isp/note"
else:
    UPLUS_RETURN_URL = "http://hanilove.co.kr/payment/uplus/return"
    UPLUS_ISPWAP_URL = "http://hanilove.co.kr/payment/uplus/isp/return"
    UPLUS_ISPCANCEL_URL = "http://hanilove.co.kr/payment/uplus/isp/cancel"
    UPLUS_ISPNOTE_URL = "http://hanilove.co.kr/payment/uplus/isp/note"