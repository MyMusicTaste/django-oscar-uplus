# -*- coding: utf-8 -*-
from django.conf.urls import patterns, include, url
from apps.app import application
from django.contrib import admin
admin.autodiscover()
from django.conf.urls.static import static
from django.conf import settings
from filebrowser.sites import site

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'handocs.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    (r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    (r'^payment/uplus/', include('uplus.urls')),
    (r'', include(application.urls)),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^mce_filebrowser/', include('mce_filebrowser.urls')),
    (r'^bbs/', include('handocs.bbs.urls')),
    (r'^recipe/', include('handocs.recipe.urls')),


) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += patterns('',
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )