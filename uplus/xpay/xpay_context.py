# -*- coding: utf-8 -*-

__author__ = 'nujabes8'

import uuid
import datetime
import hashlib
import httplib
import socket
from config_uplus import *

try:
    import simplejson as json
except:
    import json
import os
import urlparse
import urllib

class Context(object):
    HTTP_HEADERS = {
        "User-Agent": "XPayClient (1.1.5/Java)",
        "Content-Type": "application/x-www-form-urlencoded; charset=EUC-KR",
    }

    @classmethod
    def get_unique(cls):
        return str(uuid.uuid4())

    @classmethod
    def hex_encode(cls, tobe_encoded, to_uppercase):
        hex_values = []
        for each_chr in tobe_encoded:
            hex_value = hex(ord(each_chr))[2:]
            if len(hex_value) == 1:
                hex_value = "0" + hex_value
            hex_values.append(hex_value)

        encoded_value = "".join(hex_values)
        if to_uppercase:
            encoded_value = encoded_value.upper()
        return encoded_value

    def __init__(self, mid):
        self._params = []
        self._mid = mid
        self._tx_id = self._gen_tx_id()
        self._auth_code = self._gen_auth_code()
        self._status = None
        self._content_type = None
        self._response_code = None
        self._response_message = None
        self._data = None
        self._body = None
        self._is_json = False
        self._response_values = None
        self._response_names = None

        # Set default parameters
        self.set("LGD_MID", self._mid)
        self.set("LGD_TXID", self._tx_id)
        self.set("LGD_AUTHCODE", self._auth_code)

    def set(self, key, value):
        if value is None: value = ""
        self._params.append((key, value))

    def request_http(self, url):
        is_success = False

#        the_config = get_config()

        # TODO: We shuld handle verify certificate and host enabled
#        verify_cert = the_config.get_value_bool("verify_cert") and False
#        verify_host = the_config.get_value_bool("verify_host") and False
        # TODO: Should handle proxy handling

        parsed_url = urlparse.urlparse(url)
        host_url = parsed_url.path
        if parsed_url.port:
            host_url = parsed_url.hostname + ":" + str(parsed_url.port)
        else:
            host_url = parsed_url.hostname

        socket.setdefaulttimeout(timeout)

        conn = httplib.HTTPSConnection(host_url)
        params = urllib.urlencode(self._params)
        headers = self.HTTP_HEADERS.copy()

#        proxy_host, proxy_port = the_config.get_value("proxy_host"), the_config.get_value("proxy_port")
#        if proxy_host and proxy_port:
#            conn.set_tunnel(proxy_host, proxy_port)

        try:
            conn.request("POST", parsed_url.path, params, headers)

            response = conn.getresponse()
            response_headers = dict(response.getheaders())

            content_type = response_headers.get("content-type")
            data = response.read().decode("utf8")

            conn.close()

            is_success = True

            # IVars for future use
            self._status = response.status
            self._content_type = content_type.split(";")[0]
            self._data = data
        except httplib.InvalidURL:
            self._response_code = LGD_ERR_HTTP_URL
        except httplib.HTTPException:
            self._response_code = LGD_ERR_HTTP
        except Exception:
            self._response_code = LGD_ERR_INTERNAL

        return is_success

    def TX(self, url):
        is_success = self.request_http(url)
        if not is_success:
            logger.error("TX has failed with response code = %s", self._response_code)
        elif self._content_type != "application/json":
            is_success = False
            logger.error("TX has failed due to content type error: %s", self._content_type)
        else:
            self._is_json = True
            try:
                self._body = response = json.loads(self._data)
            except:
                is_success = False
                self._response_code = LGD_ERR_JSON_DECODE
                logger.error("TX has failed due to json decoder")
            else:
                self._response_code = response.get("LGD_RESPCODE")
                self._response_message = response.get("LGD_RESPMSG")
                lgd_response = response.get("LGD_RESPONSE")

                first_elm = lgd_response[0]
                response_names = first_elm.keys()
                response_values = dict(map(lambda name: (name, []), response_names))

                for elm in lgd_response:
                    for response_name in response_names:
                        response_values.get(response_name).append(elm.get(response_name))

#                for response_name, values in response_values.items():
#                    print response_name, values
#                    if self._can_log(response_name):
#                        logger.info(u"{response_name}: {response_values}".format(
#                                response_name=response_name,
#                                response_values=(u",".join(values)),
#                                ))
#                logger.info("TX has succeeded with response code = %s, response message = %s",
#                            self._response_code, self._response_message)

                self._response_values = response_values
                self._response_names = response_names

        return is_success

    @property
    def status(self):
        return self._status
    @property
    def mid(self):
        return self._mid
    @property
    def tx_id(self):
        return self._tx_id
    @property
    def content_type(self):
        return self._content_type
    @property
    def response_code(self):
        return self._response_code
    @property
    def response_message(self):
        return self._response_message
    @property
    def body(self):
        return self._body
    @property
    def is_json(self):
        return self._is_json
    @property
    def response_names(self):
        return self._response_names
    @property
    def response_name_count(self):
        return len(self._response_names)
    @property
    def response_array_count(self):
        return len(self._response_values.get(self.response_name(0)))

    def response_name(self, idx):
        return self._response_names[idx]

    def response(self, name, idx=0):
        return self._response_values.get(name)[idx]

    def _can_log(self, name):
        log_except = get_config().get_value("log_except")
        return (log_except.find(name) == -1)

    def _gen_tx_id(self):
        header = "{mid}-{server_id}-{date_string}".format(
            mid=self._mid,
            server_id=server_id,
            date_string=datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            )

        unique = self.get_unique()
        to_encode_body = header + unique

        sha1_body = hashlib.sha1(to_encode_body).digest()
        tx_id = self.hex_encode(sha1_body, False)

        return tx_id

    def _gen_auth_code(self):
        to_encode_body = self._tx_id + LGUPLUS_SECRET_MERTKEY
        sha1_body = hashlib.sha1(to_encode_body).digest()

        auth_code = self.hex_encode(sha1_body, False)
        return auth_code

#if __name__ == '__main__':
#    context = Context("t" + LGUPLUS_MID)
#    context.set("LGD_TXNAME", "Ping")
#    context.set("LGD_ERRORTYPE", None)
#    context.set("LGD_TEST", "TEST1")
#    context.set("LGD_TEST", "TEST2")
#    context.TX(test_url)
#
#    print "Status code", context.status
#    print "Content type", context.content_type
#    print "Response code", context.response_code
#    print "Response message", context.response_message
#    print "Response names", context.response_names
#    print "Name count", context.response_name_count
#    print "Response array count", context.response_array_count
#    for name in context.response_names:
#        print name,
#        for idx in range(context.response_array_count):
#            print "Response message", context.response(name, idx),
#        print ""
#
