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

LGUPLUS_MID = '' if LGUPLUS_TEST else ''
LGUPLUS_SECRET_MERTKEY = '' if LGUPLUS_TEST else ''

dacom_url = 'https://xpayclient.lgdacom.net/xpay/Gateway.do'
test_url = 'https://xpayclient.lgdacom.net:7443/xpay/Gateway.do'
aux_url = 'http://xpayclient.lgdacom.net:7080/xpay/Gateway.do'

if LGUPLUS_TEST:
    UPLUS_RETURN_URL = ""
    UPLUS_ISPWAP_URL = ""
    UPLUS_ISPCANCEL_URL = ""
    UPLUS_ISPNOTE_URL = ""
else:
    UPLUS_RETURN_URL = ""
    UPLUS_ISPWAP_URL = ""
    UPLUS_ISPCANCEL_URL = ""
    UPLUS_ISPNOTE_URL = ""
