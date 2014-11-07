# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from apps.app import application
from django.contrib import admin
admin.autodiscover()
from django.conf.urls.static import static
from django.conf import settings
from filebrowser.sites import site

urlpatterns = patterns('',
    (r'^payment/uplus/', include('uplus.urls')),
    (r'', include(application.urls)),


) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )