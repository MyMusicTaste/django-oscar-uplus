# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _, pgettext_lazy

class UplusTransaction(models.Model):
    '''
     #index - status, timestamp, buyer_name, phone_no
    '''
    PAY_STATE = (
        ('N', "New"), #구매시작
        ('A', "Auth"), #payment 정보 인증
        ('C', "Cancel"), # 구매 취소
        ('P', "Paid"),    #구매완료
        ('F', "Fail"),    #에러
        #CAS
        ('R', "CAS requested"), #가상계좌 만들어짐

    )

    amount = models.IntegerField(default=0, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now=True) #취소할것 날짜참조
    status = models.CharField(max_length=1, choices=PAY_STATE, db_index=True, default='N')
    basket_id = models.IntegerField(default=0)
    order_number = models.CharField(_("Order number"), max_length=128, db_index=True)
    #PG사용 정보 (PG사에따라 추가 가능)
    pay_key = models.CharField(max_length=128, blank=True) #auth key
    pay_type = models.CharField(max_length=20)
    tid = models.CharField(max_length=24, blank=True) #LG U transactionID
    financode = models.CharField(max_length=10, blank=True)
    financename = models.CharField(max_length=20, blank=True)
    financeauth = models.CharField(max_length=20, blank=True)
    #현금 영수증
    cashreceipt = models.BooleanField(default=True)
    error_message = models.CharField(max_length=128, blank=True)
    error_code = models.CharField(max_length=32, blank=True)
    #CAS
    amount_added = models.IntegerField(default=0, null=True, blank=True) #가상계좌 현금입고 balance
    cas_accountnum = models.CharField(max_length=64, blank=True)
    cas_log = models.CharField(max_length=512, blank=True)
    cas_payer = models.CharField(max_length=32, blank=True)
    cashreceipt_no = models.CharField(max_length=64, blank=True)
    cashreceipt_self = models.BooleanField(default=False)

    class Meta:
        app_label = 'uplus'
        ordering = ('-id',)

    def __unicode__(self):
        return str(self.amount)