# -*- coding: utf-8 -*-

import logging
from django.views.generic import RedirectView, View
from django.http import HttpResponse
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db.models import get_model
from django.utils.translation import ugettext_lazy as _
from .exceptions import *

from oscar.apps.payment.models import SourceType, Source
from oscar.core.loading import get_class
from django.views.decorators.csrf import csrf_exempt
from oscar.apps.checkout import views
from uplus.models import UplusTransaction
from datetime import datetime
from uplus.xpay.utils import _create_hash
from uplus.gateway import _pay, _cancel
from apps.uplus.calculator import RecipeOrderTotalCalculator

logger = logging.getLogger('uplus')
Selector = get_class('partner.strategy', 'Selector')
Basket = get_model('basket', 'Basket')
Applicator = get_class('offer.utils', 'Applicator')
Order = get_model('order', 'Order')
Repository = get_class('shipping.repository', 'Repository')
OrderPlacementMixin = get_class('checkout.mixins', 'OrderPlacementMixin')

class UplusReturnView(views.PaymentDetailsView):
    def check_amount_integrity(self, basket, transaction_amount):
        if basket.is_recipe:
            method = Repository().get_recipe_shipping_method(basket)
            amount = int(RecipeOrderTotalCalculator().calculate(
                basket, method).incl_tax)
        else:
            amount = int(basket.total_incl_tax)

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

        error_msg = _(
            "A problem occurred communicating with Uplus "
            "- please try again later"
        )

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
            error_msg = u"결제에 문제가 있습니다. 문제가 지속되면 문의 바랍니다. "
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
        ret = _pay(paykey, oid)
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

        source_type, is_created = SourceType.objects.get_or_create(
            name='Uplus')
        source = Source(source_type=source_type,
                        currency=total.currency,
                        amount_allocated=total.incl_tax,
                        )
        self.add_payment_source(source)
        self.add_payment_event('Pending', total.incl_tax,
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
        ret = _pay(paykey, oid)
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
            if line.stockrecord:
                line.stockrecord.cancel_allocation(qty)

    def post(self, request, *args, **kwargs):
        order_id = request.POST['order_id']
        order = Order.objects.get(id=order_id)
        self.url = reverse('customer:order', kwargs={'order_number':order.number})

        if order.status == 'Shipped':
            messages.error(request, u'이미 발송되어 취소가 불가능합니다.')
            return self.get(request, *args, **kwargs)

        transaction = UplusTransaction.objects.get(order_number=order.number)

        result, resp_code = _cancel(transaction)
        if result and resp_code == "0000":
            messages.info(request, u'취소되었습니다.')
            self.add_payment_event('Cancelled', transaction.amount)
            self.cancel_stock_allocations(order)

            return self.get(request, *args, **kwargs)
        else:
            messages.error(request, u'오류가 생겼습니다. '+ str(transaction.error_message))
            return self.get(request, *args, **kwargs)

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

