from django.conf.urls import include,url
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views

from webinterface import views as slam_views

handler404 = "webinterface.views.error_404"
handler403 = "webinterface.views.error_403"
handler500 = "webinterface.views.error_500"

urlpatterns = [
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += [
    url(r'^$', slam_views.list_pools, name="list_pools"),
    url(r'^lang/?$', slam_views.lang, name="lang"),
    url(r'^pool/?$', slam_views.list_pools, "list_pools_2"),
    url(r'^addpool/?$', slam_views.add_pool, name="add_pool"),
    url(r'^pool/([^/]+)/map/?$', slam_views.pool_map, name="pool_map"),
    url(r'^pool/([^/]+)/?$', slam_views.pool_info, name="pool_info"),
    url(r'^host/?$', slam_views.list_hosts, name="list_hosts"),
    url(r'^search/?$', slam_views.search_hosts, name="search_hosts"),
    url(r'^addhost/?$', slam_views.add_host, name="add_host"),
    url(r'^host/([^/]+)/?$', slam_views.host_info, name="host_info"),
    url(r'^address/([^/]+)/?$', slam_views.address_info, name="address_info"),
    url(r'^property/?$', slam_views.property_, name="property_"),
    url(r'^reload/?$', slam_views.reload, name="reload"),
    url(r'^logs/?$', slam_views.list_logs, name="list_logs"),
    url(r'^login/?$', slam_views.login, name="login"),
    url(r'^logout/?$', slam_views.logout, name="logout"),
]
