# -*- coding: utf-8 -*-
from django.conf.urls import *
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = patterns('',
    url(r'^return$', csrf_exempt(views.UplusReturnView.as_view()), name='uplus-return'),
    url(r'^cancel$', views.UplusCancelView.as_view(), name='uplus-cancel'),
    url(r'^popup_close$', csrf_exempt(views.UplusPopupCloseView.as_view()), name='uplus-popup-close'),
    url(r'^cas/return$', csrf_exempt(views.UplusCasReturnView.as_view()), name='uplus-cas-return'),

    url(r'^isp/return/(?P<transaction_id>\d+)$', views.UplusReturnView.as_view(), name='uplus-isp-return'),
    url(r'^isp/cancel$', views.UplusIspCancelView.as_view(), name='uplus-isp-cancel'),
    url(r'^isp/note$', csrf_exempt(views.UplusIspNoteView.as_view()), name='uplus-isp-note'),

)
