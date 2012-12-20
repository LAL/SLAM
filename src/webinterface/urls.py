from django.conf.urls import patterns, include, url
from django.conf.urls.i18n import i18n_patterns

import webinterface.views

handler404 = "webinterface.views.error_404"
handler403 = "webinterface.views.error_403"
handler500 = "webinterface.views.error_500"

urlpatterns = patterns('',
    url(r'^i18n/', include('django.conf.urls.i18n')),
)

urlpatterns += patterns('webinterface.views',
    url(r'^$', "list_pools"),
    url(r'^lang/?$', "lang"),
    url(r'^pool/?$', "list_pools"),
    url(r'^pool/([^/]+)/map/?$', "pool_map"),
    url(r'^pool/([^/]+)/?$', "pool_info"),
    url(r'^host/?$', "list_hosts"),
    url(r'^host/([^/]+)/?$', "host_info"),
    url(r'^address/([^/]+)/?$', "address_info"),
    url(r'^logs/?$', "list_logs"),
    url(r'^login/?$', "login"),
    url(r'^logout/?$', "logout"),
)
