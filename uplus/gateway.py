# -*- coding: utf-8 -*-
from uplus.xpay import config_uplus
from uplus.xpay.xpay_client import XPayClient
from uplus.models import UplusTransaction

def _pay(pay_key, basket_id):
    xpay_client = XPayClient(config_uplus.LGUPLUS_TEST)
    xpay_client.init_tx()
    xpay_client.set("LGD_TXNAME", "PaymentByKey")
    xpay_client.set("LGD_PAYKEY", pay_key)

    if xpay_client.TX():
        if xpay_client.response_code == "0000":
            ret = {}
            ret.update({'LGD_TID':xpay_client.response("LGD_TID")})
            ret.update({'LGD_FINANCECODE':xpay_client.response_with_default("LGD_FINANCECODE","")})
            ret.update({'LGD_FINANCENAME':xpay_client.response_with_default("LGD_FINANCENAME","")})
            ret.update({'LGD_FINANCEAUTHNUM':xpay_client.response_with_default("LGD_FINANCEAUTHNUM","")})
            return ret
        else:
            UplusTransaction.objects.filter(basket_id=basket_id).update(
                error_code=xpay_client.response_code,
                error_message=xpay_client.response_with_default("LGD_RESPMSG",""))
            return None

'''
cas_cancel_info
dict{
LGD_RFACCOUNTNUM
LGD_RFBANKCODE
LGD_RFCUSTOMERNAME
LGD_RFPHONE
}
'''
def _cancel(uplustransaction, cas_cancel_info = None):
    xpay_client = XPayClient(config_uplus.LGUPLUS_TEST)
    xpay_client.init_tx()

    xpay_client.set("LGD_MID", config_uplus.LGUPLUS_MID)
    xpay_client.set("LGD_TID", uplustransaction.tid)
    xpay_client.set("LGD_TXNAME", "Cancel")

    #CAS cancel info dict
    if cas_cancel_info:
        xpay_client.set("LGD_RFACCOUNTNUM", cas_cancel_info['LGD_RFACCOUNTNUM'])
        xpay_client.set("LGD_RFBANKCODE", cas_cancel_info['LGD_RFBANKCODE'])
        xpay_client.set("LGD_RFCUSTOMERNAME", cas_cancel_info['LGD_RFCUSTOMERNAME'])
        xpay_client.set("LGD_RFPHONE", cas_cancel_info['LGD_RFPHONE'])

    if xpay_client.TX():
        if xpay_client.response_code == "0000":
            uplustransaction.status = 'C'
            uplustransaction.save()
            return True, xpay_client.response_code, ""
        else:
            uplustransaction.status = 'F'
            uplustransaction.error_message = xpay_client.response_message
            uplustransaction.error_code = xpay_client.response_code
            uplustransaction.save()
            return False, xpay_client.response_code, xpay_client.response_message

    else:
        return False, "", u"LGUPLUS server respnse error"
