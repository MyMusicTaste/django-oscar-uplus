# -*- coding: utf-8 -*-

import logging
from oscar.apps.checkout import views
from uplus.xpay import config_uplus
from django.utils.translation import ugettext_lazy as _
from datetime import datetime
from .forms import UplusPayTypeForm, UplusAuthBaseForm, ShippingAddressForm
from uplus.models import UplusTransaction
from django.db import IntegrityError
from uplus.xpay.utils import _create_hash
from oscar.core.loading import get_class, get_classes
from django.views import generic
from oscar.core.loading import get_model
from oscar.apps.checkout.views import ShippingAddressView
from oscar.apps.checkout.views import ShippingMethodView
from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse, reverse_lazy

logger = logging.getLogger('uplus')
GatewayForm = get_classes('checkout.forms', ['GatewayForm'])
CheckoutSessionMixin = get_class('checkout.session', 'CheckoutSessionMixin')
UserAddress = get_model('address', 'UserAddress')
Repository = get_class('shipping.repository', 'Repository')


class PaymentDetailsView(views.PaymentDetailsView):

    def get_context_data(self, **kwargs):
        ctx = super(PaymentDetailsView, self).get_context_data(**kwargs)
        ctx['uplus_paytype_form'] = kwargs.get(
            'uplus_paytype_form', UplusPayTypeForm())
        ctx['uplus_auth_form'] = kwargs.get(
            'uplus_auth_form', UplusAuthBaseForm())

        if self.basket.is_recipe:
            method = Repository().get_recipe_shipping_method(self.basket)
            ctx['shipping_method'] = method
            ctx['shipping_price'] = method.calculate(self.basket)
            # context['shipping_methods'] = self.get_shipping_methods(
            #     self.request.basket)

            ctx['base_price'] = self.basket.get_base_price
            ctx['composition_price'] = self.basket.get_composition_price
            ctx['sweetner_price'] = self.basket.get_sweetner_price
            ctx['extra_price'] = self.basket.get_extra_price

            ctx['order_total'] = RecipeOrderTotalCalculator().calculate(
                self.request.basket, method)

            recipe_basket_form = RecipeBasketForm(instance=self.request.basket)
            ctx['recipe_basket_form'] = recipe_basket_form

        return ctx

    def get_product_description(self, basket):
        if basket.is_recipe:
            return basket.recipe_name
        else:
            index = 0
            product_info_desc = ''
            for index, line in enumerate(basket.all_lines()):
                if index == 0:
                    product = line.product
                    product_info_desc += product.get_title()

            if index > 0:
                product_info_desc += u' 외 %s개 물품' % str(index)
            return product_info_desc

    def get(self, request, *args, **kwargs):
        self.basket = self.request.basket
        return super(PaymentDetailsView, self).get(self, request, *args, **kwargs)


    def post(self, request, *args, **kwargs):
        # Override so we can validate the bankcard/billingaddress submission.
        # If it is valid, we render the preview screen with the forms hidden
        # within it.  When the preview is submitted, we pick up the 'action'
        # parameters and actually place the order.
        if request.POST.get('action', '') == 'place_order':
            return self.do_place_order(request)

        paytype_form = UplusPayTypeForm(request.POST)
        if not all([paytype_form.is_valid()]):
            # Form validation failed, render page again with errors
            self.preview = False
            ctx = self.get_context_data(
                paytype_form=paytype_form)
            return self.render_to_response(ctx)

        basket = self.request.basket
        product_info_desc = self.get_product_description(basket)
        self.basket = self.request.basket

        #create or get uplus transaction for basket id
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        if self.basket.is_recipe:
            method = Repository().get_recipe_shipping_method(self.basket)
            amount = int(RecipeOrderTotalCalculator().calculate(
                self.request.basket, method).incl_tax)
        else:
            amount = int(basket.total_incl_tax)
        # basket.freeze()

        try:
            transaction = UplusTransaction.objects.create(
                basket_id=basket.id, amount=amount, timestamp=timestamp, pay_type=paytype_form.cleaned_data['paytype']
            )
        except IntegrityError:
            transaction = UplusTransaction.objects.get(basket_id=basket.id)
            transaction.pay_type = paytype_form.cleaned_data['paytype']
            transaction.amount = amount
            transaction.timestamp = timestamp
            transaction.status = 'N'
            transaction.save()

        hash = _create_hash(str(transaction.id), amount, timestamp)

        # Render preview with bankcard and billing address details hidden
        uplus_auth_form = UplusAuthBaseForm({
               'LGD_MID':config_uplus.LGUPLUS_MID,
               'LGD_OID':transaction.id,
               'LGD_BUYER':request.user.username,
               'LGD_PRODUCTINFO': product_info_desc,
               'LGD_AMOUNT':amount,
               'LGD_BUYEREMAIL':request.user.email,
               'LGD_CUSTOM_SKIN':'cyan',
               'LGD_CUSTOM_PROCESSTYPE':'TWOTR',
               'LGD_HASHDATA':hash,
               'LGD_TIMESTAMP':timestamp,
               'LGD_CEONAME': 'Jaeseok Lee',
               'LGD_MERTNAME': "MyMusicTaste",
               'LGD_CUSTOM_LOGO':"http://media.mironi.pl/img/21_height.png",
               'LGD_ENCODING':"UTF-8",
               'LGD_ENCODING_NOTEURL':"UTF-8",
               'LGD_ENCODING_RETURNURL':"UTF-8",
               'LGD_RETURNURL':config_uplus.UPLUS_RETURN_URL,
               'LGD_VERSION':'PHP_SmartXPay_1.0',
               'LGD_CUSTOM_FIRSTPAY':paytype_form.cleaned_data['paytype'],
               'LGD_KVPMISPAUTOAPPYN':'Y',
               'LGD_CUSTOM_ROLLBACK':'Y',
               'LGD_DEFAULTCASHRECEIPTUSE':'1',
                #ISP
               'LGD_KVPMISPCANCELURL':config_uplus.UPLUS_ISPCANCEL_URL,
               'LGD_KVPMISPWAPURL':config_uplus.UPLUS_ISPCANCEL_URL+str(transaction.id),
               'LGD_KVPMISPNOTEURL':config_uplus.UPLUS_ISPNOTE_URL,
                #이체
               'LGD_MTRANSFERCANCELURL':config_uplus.UPLUS_ISPCANCEL_URL,
               'LGD_MTRANSFERWAPURL':config_uplus.UPLUS_ISPCANCEL_URL+str(transaction.id),
               'LGD_MTRANSFERNOTEURL':config_uplus.UPLUS_ISPNOTE_URL,
               'LGD_CASHRECEIPTYN':'Y',
               'LGD_CUSTOM_MERTNAME':'(주)제이제이에스미디어',
               'LGD_CUSTOM_MERTPHONE':'070-8616-6442',
               'LGD_CUSTOM_BUSINESSNUM':'220-88-29856',
               'LGD_CUSTOM_CEONAME':'이재석',
               })
        return self.render_preview(request,
                                   paytype_form=paytype_form,
                                   auth_form=uplus_auth_form,
                                   test=config_uplus.LGUPLUS_TEST,
                                   paytype=dict(paytype_form.UPLUS_PAY_TYPE)[paytype_form.cleaned_data['paytype']])
