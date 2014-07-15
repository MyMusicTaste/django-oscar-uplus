# -*- coding: utf-8 -*-
    
from django.conf import settings
import logging
from config_uplus import *
from xpay_context import Context

logger = logging.getLogger(__name__)

class XPayClient(object):
    def __init__(self, is_test=True):
        """Initialize xpay client.
        
        Args:
          home_dir: (string) Path where configuration files are stored
          mode: (string) Mode of operation (test/service)
        """
        self._is_test = is_test
        self._response_code = None
        self._response_message = None
        self._mid = LGUPLUS_MID
        
    def init_tx(self):
        self._context = Context(self._mid)
        
    def set(self, key, value):
        self._context.set(key, value)
        
    def TX(self):
        # Initialize variables
        is_success = False
        is_rollback = False
        is_reporting = False
        rollback_on_error = auto_rollback
        report_on_error = report_error
        
        # (reports)
        report_status = None
        report_message = None
        rollback_reason = None
        
        context_success = self._context.TX(self.URL)
        if not context_success:
            is_rollback = True
        elif (self._context.status < 200 or
              self._context.status >= 300):
            self._response_code = 30000 + self._context.status
            self._response_message = u"HTTP response code = {response_code}".format(response_code=self._context.status)
            
            logger.error(u"[%s] TX failed: response code = %s, response message = %d", 
                         self.tx_id, self._response_code, self._response_message)
            
            report_status = u"HTTP response {response_code}".format(response_code=self._context.status)
            report_message = self._context.body
            
            if report_on_error:
                is_rollback = True
                rollback_reason = u"HTTP {response_code}".format(response_code=self._context.status)
                
            is_reporting = True
        elif self._context.is_json:
            is_success = True
            self._response_code = self._context.response_code
            self._response_message = self._context.response_message
        elif rollback_on_error:
            is_rollback = True
            rollback_reason = u"JSON decode fail"
            
        if rollback_on_error and is_rollback:
            new_context = Context(self._mid)
            new_context.set("LGD_TXNAME", "Rollback")
            new_context.set("LGD_RB_TXID", self.tx_id)
            new_context.set("LGD_RB_REASON", rollback_reason)
            new_context.TX(self.URL)
        if report_on_error and is_reporting:
            new_context = Context(self._mid)
            new_context.set("LGD_TXNAME", "Report")
            new_context.set("LGD_STATUS", report_status)
            new_context.set("LGD_MSG", report_message)
            new_context.TX(aux_url)
            
        return is_success
    
    def rollback(self, rollback_reason):
        try:
            new_context = Context(self._mid)
            new_context.set("LGD_TXNAME", "Rollback")
            new_context.set("LGD_RB_TXID", self.tx_id)
            new_context.set("LGD_RB_REASON", rollback_reason)
            is_success = new_context.TX(self.URL)
        except:
            is_success = False
        
        if not is_success:
            logger.error("[%s] Rollback failed!", self.tx_id)
        return is_success
            
    @property
    def tx_id(self):
        return self._context.tx_id
    
    @property
    def URL(self):
        if self._is_test:
            url = test_url
        else:
            url = dacom_url
        return url
    
    @property
    def response_code(self):
        return self._response_code
    @property
    def response_message(self):
        return self._response_message
    
    @property
    def response_names(self):
        return self._context.response_names
    @property
    def response_name_count(self):
        return self._context.response_name_count
    @property
    def response_array_count(self):
        return self._context.response_array_count
    
    def response_name(self, idx):
        return self._context.response_name(idx)
    def response(self, name, idx=0):
        return self._context.response(name, idx)
    def response_with_default(self, name, default):
        try:
            response = self.response(name)
        except:
            response = default
        return response
    
#if __name__ == '__main__':
#    xpay_client = XPayClient(is_test=True)
#    xpay_client.init_tx()
#    xpay_client.set("LGD_TXNAME", "Ping")
#    xpay_client.set("LGD_DUMMY", "=+A\uAC00\uB098\uB2E4")
#    xpay_client.set("LGD_RESULTCNT", "3");
#    xpay_client.TX()
