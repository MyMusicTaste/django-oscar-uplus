# -*- coding: utf-8 -*-
__author__ = 'nujabes8'
from django import forms
from django.utils.translation import ugettext_lazy as _
from uplus.xpay.config_uplus import UPLUS_RETURN_URL
from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

class UplusPayTypeForm(forms.Form):
    UPLUS_PAY_TYPE = (
        ('SC0010', _("Credit Card")), #신용카드
        ('SC0030', _("Transfer Cash")), #계좌이체
        ('SC0060', _("Cell Phone")), #휴대폰
    )
    paytype = forms.ChoiceField(choices=UPLUS_PAY_TYPE,
                                show_hidden_initial=True,
                                label=_('Payment Method'),
                                required=True,
                                error_messages = {
                                    'invalid_choice': 'form_invalid',
                                    'required': 'required',
                                },)


class UplusAuthBaseForm(forms.Form):
    LGD_MID = forms.CharField(
        label ="LGD_MID",
        widget = forms.HiddenInput(),
    )

    LGD_OID = forms.CharField(
        label ="LGD_OID",
        widget = forms.HiddenInput(),
        required=False
    )

    LGD_AMOUNT = forms.CharField(
        label ="LGD_AMOUNT",
        widget = forms.HiddenInput(),
        required=False
    )

    LGD_BUYER = forms.CharField(
        label ="LGD_BUYER",
        widget = forms.HiddenInput(),
        required=False
    )

    LGD_PRODUCTINFO = forms.CharField(
        label ="LGD_PRODUCTINFO",
        widget = forms.HiddenInput(),
        required=False
    )

    LGD_HASHDATA = forms.CharField(
        label ="LGD_HASHDATA",
        widget = forms.HiddenInput(),
        required=False

    )

    LGD_RETURNURL = forms.CharField(
        label ="LGD_RETURNURL",
        widget = forms.HiddenInput(),
        initial = UPLUS_RETURN_URL
    )

    LGD_BUYERADDRESS = forms.CharField(
        label ="LGD_BUYERADDRESS",
        required=False,
        widget = forms.HiddenInput(),

    )

    LGD_BUYERPHONE = forms.CharField(
        label ="LGD_BUYERPHONE",
        widget = forms.HiddenInput(),
        required=False
    )

    LGD_BUYEREMAIL = forms.CharField(
        label ="이메일주소",
        widget = forms.HiddenInput(),

    )

    LGD_PRODUCTCODE = forms.CharField(
        label ="LGD_PRODUCTCODE",
        required=False,
        widget = forms.HiddenInput(),
    )

    LGD_CUSTOM_FIRSTPAY = forms.CharField(
        label ="LGD_CUSTOM_FIRSTPAY",
        widget = forms.HiddenInput(),
    )

    LGD_CUSTOM_PROCESSTYPE = forms.CharField(
        label ="LGD_CUSTOM_PROCESSTYPE",
        initial = "TWOTR",
        widget = forms.HiddenInput(),
    )

    LGD_CUSTOM_SKIN = forms.CharField(
        label ="LGD_CUSTOM_SKIN",
        initial = "cyan",
        widget = forms.HiddenInput(),
    )

    LGD_CEONAME = forms.CharField(
        label ="LGD_CEONAME",
        initial = "Jaeseok Lee",
        widget = forms.HiddenInput(),
    )

    LGD_MERTNAME = forms.CharField(
        label ="LGD_MERTNAME",
        initial = "MyMusicTaste",
        widget = forms.HiddenInput(),
    )

    LGD_CUSTOM_LOGO = forms.CharField(
        label ="LGD_CUSTOM_LOGO",
        initial = "http://media.mironi.pl/img/21_height.png",
        widget = forms.HiddenInput(),
    )

    LGD_ENCODING = forms.CharField(
        label ="LGD_ENCODING",
        initial = "UTF-8",
        widget = forms.HiddenInput(),
    )

    LGD_ENCODING_NOTEURL = forms.CharField(
        label ="LGD_ENCODING_NOTEURL",
        initial = "UTF-8",
        widget = forms.HiddenInput(),
    )

    LGD_ENCODING_RETURNURL = forms.CharField(
        label ="LGD_ENCODING_RETURNURL",
        initial = "UTF-8",
        widget = forms.HiddenInput(),
    )

    LGD_VERSION = forms.CharField(
        label ="LGD_VERSION",
        initial = "PHP_SmartXPay_1.0",
        widget = forms.HiddenInput(),
    )

    LGD_TIMESTAMP = forms.CharField(
        label ="LGD_TIMESTAMP",
        widget = forms.HiddenInput(),
        required=False
    )
    ###########################################################

    # ISP
    LGD_KVPMISPWAPURL = forms.CharField(
        label ="LGD_KVPMISPWAPURL",
        widget = forms.HiddenInput(),
    ) #isp 성공

    LGD_KVPMISPCANCELURL = forms.CharField(
        label ="LGD_KVPMISPCANCELURL",
        widget = forms.HiddenInput(),
    ) #isp 캔슬

    LGD_KVPMISPNOTEURL = forms.CharField(
        label ="LGD_KVPMISPNOTEURL",
        widget = forms.HiddenInput(),
    ) #isp DB처리페이지

    #계좌이체용
    LGD_MTRANSFERWAPURL = forms.CharField(
        label ="LGD_MTRANSFERWAPURL",
        widget = forms.HiddenInput(),
    ) #isp 성공

    LGD_MTRANSFERCANCELURL = forms.CharField(
        label ="LGD_MTRANSFERCANCELURL",
        widget = forms.HiddenInput(),
    ) #isp 캔슬

    LGD_MTRANSFERNOTEURL = forms.CharField(
        label ="LGD_MTRANSFERNOTEURL",
        widget = forms.HiddenInput(),
    ) #isp DB처리페이지

    LGD_DEFAULTCASHRECEIPTUSE = forms.CharField(
        label ="LGD_DEFAULTCASHRECEIPTUSE",
        widget = forms.HiddenInput(),
        initial='1'

    )

    LGD_DEFAULTCASHRECEIPTUSE = forms.CharField(
        label ="LGD_DEFAULTCASHRECEIPTUSE",
        widget = forms.HiddenInput(),
        initial='1'

    )


#    (주의)LGD_CUSTOM_ROLLBACK 의 값을  "Y"로 넘길 경우, LG U+ 전자결제에서 보낸 ISP(국민/비씨)
#    승인정보를 고객서버의 note_url에서 수신시  "OK" 리턴이 안되면  해당 트랜잭션은  무조건 롤백(자동취소)처리되고,
#    LGD_CUSTOM_ROLLBACK 의 값 을 "C"로 넘길 경우, 고객서버의 note_url에서 "ROLLBACK"
#    리턴이 될 때만 해당 트랜잭션은  롤백처리되며  그외의 값이 리턴되면 정상 승인완료 처리됩니다.
#    만일, LGD_CUSTOM_ROLLBACK 의 값이 "N" 이거나 null 인 경우,
#    고객서버의 note_url에서  "OK" 리턴이  안될시, "OK" 리턴이 될 때까지 3분간격으로 2시간동안  승인결과를 재전송합니다.

    LGD_KVPMISPAUTOAPPYN = forms.CharField(
        label ="LGD_KVPMISPAUTOAPPYN",
        widget = forms.HiddenInput(),
        initial='Y'
    ) #isp 비동기 처리여부

    LGD_CUSTOM_ROLLBACK = forms.CharField(
        label ="LGD_KVPMISPAUTOAPPYN",
        widget = forms.HiddenInput(),
        initial='Y'
    ) #isp 비동기 롤백 처리여부

    LGD_CASHRECEIPTYN = forms.CharField(
        label ="LGD_CASHRECEIPTYN",
        widget = forms.HiddenInput(),
    ) #isp 비동기 롤백 처리여부

    #상점정보
    LGD_CUSTOM_MERTNAME = forms.CharField(
        label ="LGD_CUSTOM_MERTNAME",
        widget = forms.HiddenInput(),
        initial='(주)제이제이에스미디어'
    )

    LGD_CUSTOM_MERTPHONE = forms.CharField(
        label ="LGD_CUSTOM_MERTPHONE",
        widget = forms.HiddenInput(),
        initial='070-8616-6442'
    )

    LGD_CUSTOM_BUSINESSNUM = forms.CharField(
        label ="LGD_CUSTOM_BUSINESSNUM",
        widget = forms.HiddenInput(),
        initial='220-88-29856'
    )

    LGD_CUSTOM_CEONAME = forms.CharField(
        label ="LGD_CUSTOM_CEONAME",
        widget = forms.HiddenInput(),
        initial='이재석'
    )

User = get_user_model()
Country = get_model('address', 'Country')
