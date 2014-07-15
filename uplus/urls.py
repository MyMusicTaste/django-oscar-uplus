# -*- coding: utf-8 -*-
from django.conf.urls import *
from django.views.decorators.csrf import csrf_exempt

from . import views

urlpatterns = patterns('',
    url(r'^return$', csrf_exempt(views.UplusReturnView.as_view()), name='uplus-return'),
    url(r'^cancel$', views.UplusCancelView.as_view(), name='uplus-cancel'),
    url(r'^isp/return/(?P<transaction_id>\d+)$', views.UplusReturnView.as_view(), name='uplus-isp-return'),
    url(r'^isp/cancel$', views.UplusIspCancelView.as_view(), name='uplus-isp-cancel'),
    url(r'^isp/note$', csrf_exempt(views.UplusIspNoteView.as_view()), name='uplus-isp-note'),

)
