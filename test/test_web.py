import json, urllib, cookielib, urllib2, sys
from slam.models import Pool, Host, Address, Property
from slam import interface, generator
import django.contrib.auth.models


HTTP_OPENER = None


def request(url, method, data=None):
    url = "http://127.0.0.1:8737" + url
    if data:
        request = urllib2.Request(url, data=urllib.urlencode(data))
        request.add_header('Content-Type', 'application/x-www-form-urlencoded')
    else:
        request = urllib2.Request(url)
    request.get_method = lambda: method
    return HTTP_OPENER.open(request)


def setup():
    Address.objects.all().delete()
    Host.objects.all().delete()
    Pool.objects.all().delete()

    su = django.contrib.auth.models.User(username="root")
    su.set_password("rootpw")
    su.is_superuser = True
    su.is_staff = True
    su.save()

    class IgnoreErrors(urllib2.BaseHandler):
        def _ignore(self, request, response, code, msg, hdrs):
            return response
        http_error_400 = _ignore
        http_error_404 = _ignore
        http_error_409 = _ignore
    class IgnoreRedirects(urllib2.HTTPRedirectHandler):
        def _ignore(self, request, response, code, msg, hdrs):
            return response
        http_error_300 = _ignore
        http_error_301 = _ignore
        http_error_302 = _ignore
        http_error_303 = _ignore
        http_error_307 = _ignore
    jar = cookielib.CookieJar()
    global HTTP_OPENER
    HTTP_OPENER = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar),
        IgnoreRedirects, IgnoreErrors)
    request("/login", "POST", {"username": "root", "password": "rootpw"})


def run_request(method, url, data=None):
    req = request(url, method, data)
    assert req.code == 200


def status_request(method, url, data=None, status=200):
    req = request(url, method, data)
    assert req.code == status


def get_request(url):
    req = request(url, "GET")
    assert req.code == 200
    res = json.loads(req.read())
    return res


def test_poollist():
    res = get_request("/pool?format=json")
    assert len(res) == 0

    run_request("POST", "/addpool",
        {"name": "poollist1", "definition": "127.0.0.0/8"})
    run_request("POST", "/addpool",
        {"name": "poollist2", "definition": "fe80::/7"})

    res = get_request("/pool?format=json")
    assert len(res) == 2
    assert res[0]["name"] == "poollist1"
    assert res[0]["definition"] == "127.0.0.0/8"
    assert res[1]["name"] == "poollist2"
    assert res[1]["definition"] == "fe00:0000:0000:0000:0000:0000:0000:0000/7"


def test_hostlist():
    res = get_request("/host?format=json")
    assert len(res) == 0

    run_request("POST", "/addhost", {"name": "host1",
        "pool_name": "poollist1", "mac": "macaddr1"})
    run_request("POST", "/addhost", {"name": "host2",
        "pool_name": "poollist1"})

    res = get_request("/host?format=json")
    assert len(res) == 2
    assert res[0]["name"] == "host1"
    assert res[0]["addresses"][0]["address"] == "127.0.0.0"
    assert res[1]["name"] == "host2"
    assert res[1]["addresses"][0]["address"] == "127.0.0.1"


def test_pool():
    run_request("POST", "/addpool", {"name": "pooltest1",
        "definition": "1.2.3.0/24", "category": "testcat"})
    run_request("POST", "/addhost", {"name": "host3", "pool_name": "pooltest1"})

    res = get_request("/pool/pooltest1?format=json")
    assert res["name"] == "pooltest1"
    assert res["definition"] == "1.2.3.0/24"
    assert res["address_used"] == 1
    assert res["address_available"] == 2 ** 8
    assert res["category"] == "testcat"
    assert res["addresses"][0]["address"] == "1.2.3.0"
    assert res["addresses"][0]["host"] == "host3"

    run_request("PUT", "/pool/pooltest1", {"newname": "pooltest2",
        "category": "testcat2"})
    res = get_request("/pool/pooltest2?format=json")
    assert res["name"] == "pooltest2"
    assert res["category"] == "testcat2"

    run_request("DELETE", "/pool/pooltest2")
    status_request("GET", "/pool/pooltest2", status=404)


def test_pool_error():
    status_request("GET", "/pool/inexistant", status=404)
    status_request("DELETE", "/pool/inexistant", status=404)
    status_request("POST", "/addpool", status=400)

    run_request("POST", "/addpool",
        {"name": "pooltest4", "definition": "1.2.3.0/24"})
    status_request("POST", "/addpool", {"name": "pooltest4",
        "definition": "1.2.3.0/24"}, status=409)

    status_request("PUT", "/pool/pooltest4", status=400)


def test_host():
    run_request("POST", "/addpool", {"name": "pooltest3",
        "definition": "172.16.0.0/12", "category": "testcat3"})
    run_request("POST", "/addhost",
        {"name": "host4", "pool_name": "pooltest3"})
    run_request("POST", "/addhost", {"name": "host5",
        "category": "testcat3", "address": "172.31.42.42", "mac": "mac42"})

    res = get_request("/host/host4?format=json")
    assert res["name"] == "host4"
    assert res["addresses"][0]["address"] == "172.16.0.0"
    assert res["addresses"][0]["pool"] == "pooltest3"

    res = get_request("/host/host5?format=json")
    assert res["name"] == "host5"
    assert res["addresses"][0]["address"] == "172.31.42.42"
    assert res["addresses"][0]["pool"] == "pooltest3"
    assert res["addresses"][0]["mac"] == "mac42"

    run_request("PUT", "/host/host5",
        {"newname": "host6", "macaddr": "mac1337"})
    res = get_request("/host/host6?format=json")
    assert res["name"] == "host6"
    assert res["addresses"][0]["address"] == "172.31.42.42"
    assert res["addresses"][0]["mac"] == "mac1337"

    run_request("DELETE", "/host/host6")
    status_request("GET", "/pool/host6", status=404)


def test_host_error():
    status_request("GET", "/host/inexistant", status=404)
    status_request("DELETE", "/host/inexistant", status=404)

    status_request("POST", "/addhost", status=400)

    run_request("POST", "/addhost", {"name": "host7", "pool_name": "pooltest3"})
    status_request("POST", "/addhost", {"name": "host7",
        "pool_name": "pooltest3"}, status=409)

    status_request("PUT", "/host/host7", status=400)


def test_address():
    run_request("POST", "/addpool",
        {"name": "pooltest10", "definition": "10.13.10.0/24"})
    run_request("POST", "/addhost", {"name": "host20", "pool_name": "pooltest10"})

    res = get_request("/address/10.13.10.0?format=json")
    assert res["address"] == "10.13.10.0"
    assert res["pool"] == "pooltest10"
    assert res["host"] == "host20"

    run_request("DELETE", "/address/10.13.10.0")

    res = get_request("/host/host20?format=json")
    assert res["name"] == "host20"
    assert len(res["addresses"]) == 0
