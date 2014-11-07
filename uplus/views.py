# -*- coding: utf-8 -*-

import logging
from django.views.generic import RedirectView, View
from django.http import HttpResponse
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db.models import get_model
from .exceptions import *
from django.shortcuts import render_to_response
from django.template import RequestContext

from oscar.apps.payment.models import SourceType, Source
from oscar.core.loading import get_class
from django.views.decorators.csrf import csrf_exempt
from oscar.apps.checkout import views
from uplus.models import UplusTransaction
from datetime import datetime
from uplus.xpay.utils import _create_hash
from uplus.gateway import _pay, _cancel
from apps.uplus.calculator import RecipeOrderTotalCalculator
from apps.uplus.forms import UplusPayTypeForm

from django.conf import settings
from django.core.mail import EmailMessage

OrderCreator = get_class('order.utils', 'OrderCreator')
logger = logging.getLogger('uplus')
Selector = get_class('partner.strategy', 'Selector')
Basket = get_model('basket', 'Basket')
Applicator = get_class('offer.utils', 'Applicator')
Order = get_model('order', 'Order')
Repository = get_class('shipping.repository', 'Repository')
OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')
PaymentEventType = get_model('order','PaymentEventType')

class UplusReturnView(views.PaymentDetailsView):
    def check_amount_integrity(self, basket, transaction_amount):
        if basket.is_recipe:
            method = Repository().get_recipe_shipping_method(basket)
            amount = int(RecipeOrderTotalCalculator().calculate(
                basket, method).incl_tax)
        else:
            shipping_price = Repository().get_shipping_methods(None, basket)[0]
            amount = int(basket.total_incl_tax) + shipping_price.charge_incl_tax

        return amount == transaction_amount


    def get(self, request, *args, **kwargs):

        #isp redirection
        if 'transaction_id' in kwargs:
            uplustransaction = UplusTransaction.objects.get(id=kwargs['transaction_id'])
            basket = self.load_basket(uplustransaction.basket_id)
            submission = self.build_submission(basket=basket,
                       payment_kwargs={'transaction_id':uplustransaction.id})

            return self.submit(**submission)
        else:
            error_msg = u"티켓 결제에 문제가 있습니다. 문제가 지속되면 문의 바랍니다."
            messages.error(self.request, error_msg)
            return HttpResponseRedirect(reverse('checkout:payment-details'))

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        error_msg = u"티켓 결제에 문제가 있습니다. 문제가 지속되면 문의 바랍니다."

        try:
            code = request.POST['LGD_RESPCODE']
            oid = request.POST['LGD_OID']
            hash_data = request.POST['LGD_HASHDATA']
            amount = request.POST['LGD_AMOUNT']
            timestamp = request.POST['LGD_TIMESTAMP']
            message = request.POST['LGD_RESPMSG']
            uplustransaction = UplusTransaction.objects.get(id=oid)
            basket = self.load_frozen_basket(uplustransaction.basket_id)
            pay_type = request.POST['LGD_PAYTYPE']
        except Exception, e:
            error_msg = u"결제에 문제가 있습니다. 문제가 지속되면 문의 바랍니다. " + request.POST['LGD_RESPMSG']
            messages.error(self.request, error_msg)
            return HttpResponseRedirect(reverse('checkout:payment-details'))

        if code != '0000':
            uplustransaction.error_code = code
            uplustransaction.error_message = message
            uplustransaction.pay_type = pay_type
            uplustransaction.save()
            basket = self.load_basket(uplustransaction.basket_id)
            basket.thaw()
            error_msg = u"결제에 문제가 있습니다. 문제가 지속되면 문의 바랍니다. : "+ message
            messages.error(self.request, error_msg)
            return HttpResponseRedirect(reverse('checkout:payment-details'))
        else:
            basket = self.load_basket(uplustransaction.basket_id)
            basket.freeze()
            hash_data2 = _create_hash(str(oid), amount, timestamp, code)
            if hash_data2 == hash_data and self.check_amount_integrity(basket, uplustransaction.amount):
                paykey = request.POST['LGD_PAYKEY']
                uplustransaction.pay_key = paykey
                uplustransaction.status = 'A'
                uplustransaction.timestamp = datetime.now()
                uplustransaction.pay_type = pay_type
                uplustransaction.save()
            else:
                basket.thaw()
                error_msg = u"티켓 결제에 문제가 있습니다. 문제가 지속되면 문의 바랍니다."
                messages.error(self.request, error_msg)
                return HttpResponseRedirect(reverse('checkout:payment-details'))

        ##########################
        # PAY
        ##########################
        ret = _pay(paykey, uplustransaction)
        if ret and uplustransaction:
            #if CAS, casnote url will change transactiondata
            if pay_type != 'SC0040':
                uplustransaction.tid = ret['LGD_TID']
                uplustransaction.financode=ret['LGD_FINANCECODE']
                uplustransaction.financename=ret['LGD_FINANCENAME']
                try:
                    uplustransaction.financeauth=request.POST['LGD_FINANCEAUTHNUM']
                except:
                    uplustransaction.financeauth="N/A"
                uplustransaction.status='P'
                uplustransaction.save()

            basket = self.load_basket(uplustransaction.basket_id)
            if not basket:
                messages.error(self.request, error_msg)
                return HttpResponseRedirect(reverse('basket:summary'))

            submission = self.build_submission(basket=basket,
                                               payment_kwargs={'transaction_id':uplustransaction.id})
            if basket.is_recipe:
                method = Repository().get_recipe_shipping_method(basket)
                submission['shipping_method'] = method
                # submission.update({'shipping_charge':method.calculate(basket)})
                # submission['shipping_charge'] = method.calculate(basket)
                submission['order_total'] = RecipeOrderTotalCalculator().calculate(
                                                    basket, method)
                if pay_type != 'SC0040':
                    submission['order_kwargs'].update({'status':'Complete'})

            return self.submit(**submission)
        else:
            uplustransaction.pay_key = paykey
            uplustransaction.status = 'F'
            uplustransaction.timestamp = datetime.now()
            uplustransaction.save()
            basket.thaw()
        messages.error(self.request, error_msg)
        return HttpResponseRedirect(reverse('checkout:payment-details'))

    def load_frozen_basket(self, basket_id):
        # Lookup the frozen basket that this txn corresponds to
        try:
            basket = Basket.objects.get(id=basket_id, status=Basket.FROZEN)
        except Basket.DoesNotExist:
            return None

        # Assign strategy to basket instance
        if Selector:
            basket.strategy = Selector().strategy(self.request)

        # Re-apply any offers
        Applicator().apply(self.request, basket)

        return basket

    def load_basket(self, basket_id):
        # Lookup the frozen basket that this txn corresponds to
        try:
            basket = Basket.objects.get(id=basket_id)
        except Basket.DoesNotExist:
            return None

        # Assign strategy to basket instance
        if Selector:
            basket.strategy = Selector().strategy(self.request)

        # Re-apply any offers
        Applicator().apply(self.request, basket)
        return basket

    def handle_payment(self, order_number, total, **kwargs):
        transaction_id = kwargs.get('transaction_id', None)
        if transaction_id:
            uplustransaction = UplusTransaction.objects.get(id=transaction_id)
            uplustransaction.order_number=order_number
            uplustransaction.save()
            basket = self.load_frozen_basket(uplustransaction.basket_id)
            basket.submit()
        else:
            raise UplusError(u'Transaction id missing.')

        pay_type_to_string = dict(UplusPayTypeForm.UPLUS_PAY_TYPE)[uplustransaction.pay_type]

        source_type, is_created = SourceType.objects.get_or_create(
            name='Uplus '+ pay_type_to_string)
        source = Source(source_type=source_type,
                        currency=total.currency,
                        amount_allocated=total.incl_tax,
                        )
        self.add_payment_source(source)
        if uplustransaction.pay_type == 'SC0040':
            self.add_payment_event('Pending', total.incl_tax,
                               reference=order_number)
        else:
            self.add_payment_event('Complete', total.incl_tax,
                               reference=order_number)


class UplusIspNoteView(View):

    def check_amount_integrity(self, basket, transaction_amount):
        if basket.is_recipe:
            method = Repository().get_recipe_shipping_method(basket)
            amount = int(RecipeOrderTotalCalculator().calculate(
                basket, method).incl_tax)
        else:
            amount = int(basket.total_incl_tax)
        return amount == transaction_amount

    @csrf_exempt
    def post(self, request,  *args, **kwargs):
        try:
            code = request.POST['LGD_RESPCODE']
            oid = request.POST['LGD_OID']
            hash_data = request.POST['LGD_HASHDATA']
            amount = request.POST['LGD_AMOUNT']
            timestamp = request.POST['LGD_TIMESTAMP']
            message = request.POST['LGD_RESPMSG']
            uplustransaction = UplusTransaction.objects.get(id=oid)
            basket = self.load_frozen_basket(uplustransaction.basket_id)
            pay_type = request.POST['LGD_PAYTYPE']
        except:
            return HttpResponse("NOT OK")

        if code != '0000':
            uplustransaction.error_code = code
            uplustransaction.error_message = message
            uplustransaction.pay_type = pay_type
            uplustransaction.save()
            basket.thaw()
            return HttpResponse("NOT OK")
        else:
            # basket = self.load_basket(uplustransaction.basket_id)
            basket.freeze()
            hash_data2 = _create_hash(str(oid), amount, timestamp, code)
            if hash_data2 == hash_data and self.check_amount_integrity(basket, uplustransaction.amount):
                paykey = request.POST['LGD_PAYKEY']
                uplustransaction.pay_key = paykey
                uplustransaction.status = 'A'
                uplustransaction.timestamp = datetime.now()
                uplustransaction.pay_type = pay_type
                uplustransaction.save()
            else:
                basket.thaw()
                return HttpResponse("NOT OK")

        ##########################
        # PAY
        ##########################
        ret = _pay(paykey, uplustransaction)
        if ret and uplustransaction:
            uplustransaction.tid = ret['LGD_TID']
            uplustransaction.financode=ret['LGD_FINANCECODE']
            uplustransaction.financename=ret['LGD_FINANCENAME']
            try:
                uplustransaction.financeauth=request.POST['LGD_FINANCEAUTHNUM']
            except:
                uplustransaction.financeauth="N/A"
            uplustransaction.status='P'
            uplustransaction.save()

            return HttpResponse("OK")
        else:
            uplustransaction.pay_key = paykey
            uplustransaction.status = 'F'
            uplustransaction.timestamp = datetime.now()
            uplustransaction.save()
            basket.thaw()
        return HttpResponse("NOT OK")

class UplusPopupCloseView(View):
    def get(self, request):
        return HttpResponse("OK")

    def post(self, request):

        resp_code =request.POST['LGD_RESPCODE']
        if resp_code != '0000':
            return render_to_response('checkout/popup_close.html',
                                {
                                'code':request.POST['LGD_RESPCODE'],
                                'oid':request.POST['LGD_OID'],
                                'message':request.POST['LGD_RESPMSG'],
                                },
                                context_instance=RequestContext(request))
        #successful return
        return render_to_response('checkout/popup_close.html',
                                {
                                'code':request.POST['LGD_RESPCODE'],
                                'oid':request.POST['LGD_OID'],
                                'hash_data':request.POST.get('LGD_HASHDATA',''),
                                'amount':request.POST['LGD_AMOUNT'],
                                'timestamp':request.POST['LGD_TIMESTAMP'],
                                'message':request.POST['LGD_RESPMSG'],
                                'LGD_FINANCEAUTHNUM':request.POST.get('LGD_FINANCEAUTHNUM',''),
                                'LGD_PAYTYPE':request.POST.get('LGD_PAYTYPE',''),
                                'LGD_PAYKEY':request.POST.get('LGD_PAYKEY',''),
                                },
                                context_instance=RequestContext(request))


class UplusIspCancelView(RedirectView):

    permanent = False

    def get(self, request,  *args, **kwargs):
        error_msg = u'결제가 중단되었습니다.'
        is_recipe = request.session.get('is_recipe', False)
        basket = Basket.objects.get(owner=request.user, is_recipe=is_recipe, status=Basket.FROZEN)
        basket.thaw()
        messages.error(self.request, error_msg)
        return HttpResponseRedirect(reverse('checkout:payment-details'))

class UplusCancelView(OrderPlacementMixin, RedirectView):

    permanent = False

    def cancel_stock_allocations(self, order):
        lines = order.lines.all()
        line_quantities = []
        for line in lines:
            qty = line.quantity
            line_quantities.append(qty)

        for line, qty in zip(lines, line_quantities):
            try:
                for line, qty in zip(lines, line_quantities):
                    if line.stockrecord:
                        line.stockrecord.cancel_allocation(qty)
            except:
                #TODO need to verify why there is no record
                raise Exception("there is no stockrecord")

    def post(self, request, *args, **kwargs):
        order_id = request.POST['order_id']

        #########
        #TODO: NEED TO refactor
        accout_num = request.POST.get('accout_num',None)
        bank_code = request.POST.get('bank_code',None)
        phone =request.POST.get('phone',None)
        name = request.POST.get('name',None)
        cas_cancel_info = None

        if accout_num:
            cas_cancel_info = {}
            cas_cancel_info['LGD_RFACCOUNTNUM'] = accout_num
            cas_cancel_info['LGD_RFBANKCODE'] = bank_code
            cas_cancel_info['LGD_RFCUSTOMERNAME'] = name
            cas_cancel_info['LGD_RFPHONE'] = phone
        ############
        order = Order.objects.get(id=order_id)
        self.url = reverse('customer:order', kwargs={'order_number':order.number})

        if order.status == 'Shipped':
            messages.error(request, u'이미 발송되어 취소가 불가능합니다.')
            return self.get(request, *args, **kwargs)

        transaction = UplusTransaction.objects.get(order_number=order.number)

        result, resp_code, resp_message = _cancel(transaction, cas_cancel_info)
        if result and resp_code == "0000":
            messages.info(request, u'취소되었습니다.')
            order.status = 'Cancelled'
            order.set_status('Cancelled')
            order.save()

            self.cancel_stock_allocations(order)
            pay_event_type, __ = PaymentEventType.objects.get_or_create(name='Cancelled')
            self.create_payment_event(order, pay_event_type, transaction.amount, reference="취소")
            return self.get(request, *args, **kwargs)
        else:
            messages.error(request, u'오류가 생겼습니다. : '+ str(resp_message))
            return self.get(request, *args, **kwargs)


    def create_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        reference = kwargs.get('reference', "")
        event = order.payment_events.create(
            event_type=event_type, amount=amount, reference=reference)
        if lines and line_quantities:
            for line, quantity in zip(lines, line_quantities):
                event.line_quantities.create(
                    line=line, quantity=quantity)
        return event

class UplusCasReturnView(OrderPlacementMixin, View):

    @csrf_exempt
    def post(self, request):

        try:
            code = request.POST['LGD_RESPCODE']
            oid = request.POST['LGD_OID']
            hash_data = request.POST['LGD_HASHDATA']
            amount = request.POST['LGD_AMOUNT']
            timestamp = request.POST['LGD_TIMESTAMP']
            message = request.POST['LGD_RESPMSG']
            tid = request.POST['LGD_TID']
            cflag = request.POST['LGD_CASFLAG']

            uplustransaction = UplusTransaction.objects.get(id=oid)
        except Exception, e:
            return HttpResponse("NOT OK")

        payment_done = False

        hash_data2 = _create_hash(str(oid), amount, timestamp, code)
        if hash_data2 == hash_data:
            if code == '0000':
                if "R" == cflag:
                    #Created CAS account
                    uplustransaction.status = 'R'
                    uplustransaction.tid = tid
                    uplustransaction.financode = request.POST['LGD_FINANCECODE']
                    uplustransaction.financeauth = request.POST['LGD_FINANCENAME']
                    uplustransaction.amount_added = 0
                    uplustransaction.cas_accountnum = request.POST['LGD_ACCOUNTNUM']
                    uplustransaction.cas_payer = request.POST['LGD_PAYER']
                    uplustransaction.save()

                elif("I" == cflag):
                    # fund added
                    if request.POST['LGD_CASTAMOUNT'] == request.POST['LGD_CASCAMOUNT']:
                        #fully paid
                        uplustransaction.status = 'P'
                        payment_done = True
                    else:
                        #partial payment
                        uplustransaction.status = 'R'
                        order = Order.objects.get(number=uplustransaction.order_number)
                        pay_event_type, __ = PaymentEventType.objects.get_or_create(name='Pending')
                        self.create_payment_event(order, pay_event_type, request.POST['LGD_CASCAMOUNT'], reference=uplustransaction.order_number)

                    uplustransaction.amount_added = int(uplustransaction.amount_added) + int(request.POST['LGD_CASCAMOUNT'])
                    #TODO: normalize payment sequence data
                    log = uplustransaction.cas_log
                    uplustransaction.cas_log = log + ", " + request.POST['LGD_CASSEQNO'] + " - " + request.POST['LGD_CASCAMOUNT']
                    uplustransaction.save()

                    if payment_done:
                        order = Order.objects.get(number=uplustransaction.order_number)
                        order.status = 'Complete'
                        order.set_status('Complete')
                        order.save()

                        pay_event_type, __ = PaymentEventType.objects.get_or_create(name='Complete')
                        self.create_payment_event(order, pay_event_type, uplustransaction.amount, reference=uplustransaction.order_number)
                        messages = {}

                        messages['subject'] = '주문번호: #' +order.number+ '가상계좌입금완료'
                        messages['body'] = '주문번호: #' +order.number+ '가상계좌입금완료되었습니다.\n'+ 'http://hanilove.co.kr/dashboard/orders/'+str(order.number)
                        email = EmailMessage(messages['subject'],
                                 messages['body'],
                                 from_email=settings.OSCAR_FROM_EMAIL,
                                 to=settings.OSCAR_CAS_REPORT_EMAIL)
                        email.send()

                elif("C" == cflag):
                    #cancel 가상계좌
                    uplustransaction.timestamp = datetime.now()
                    uplustransaction.status = 'C'
                    uplustransaction.tid = tid
                    uplustransaction.save()

                    order = Order.objects.get(number=uplustransaction.order_number)
                    order.status = 'Cancelled'
                    order.set_status('Cancelled')

                    order.save()

                    pay_event_type, __ = PaymentEventType.objects.get_or_create(name='Cancelled')
                    self.create_payment_event(order, pay_event_type, uplustransaction.amount, reference="계좌취소")
                else:
                    return HttpResponse("cflag inconsistent")

                return HttpResponse("OK")
            else:
                uplustransaction.error_code = code
                uplustransaction.error_message = message
                uplustransaction.timestamp = datetime.now()
                uplustransaction.save()
                return HttpResponse("OK")
        else:
            return HttpResponse("Hashdata inconsistent")

        return HttpResponse("OK")

    def create_payment_event(self, order, event_type, amount, lines=None,
                             line_quantities=None, **kwargs):
        reference = kwargs.get('reference', "")
        event = order.payment_events.create(
            event_type=event_type, amount=amount, reference=reference)
        if lines and line_quantities:
            for line, quantity in zip(lines, line_quantities):
                event.line_quantities.create(
                    line=line, quantity=quantity)
        return event

'''
        Partial Cancel Logic
        if cancel_price == 0:
            모두취소
            xpay_client.set("LGD_TXNAME", "Cancel")
        else:
            #부분취소
            xpay_client.set("LGD_TXNAME", "PartialCancel")
            xpay_client.set("LGD_CANCELAMOUNT", cancel_price) #amount 취소금액 부분취소금액
            xpay_client.set("LGD_CANCELREASON", "User Cancel")
'''

