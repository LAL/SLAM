"""Webinterface view functions."""

import os, subprocess, sys, re

from django.shortcuts import render_to_response, render, redirect
from django.shortcuts import get_object_or_404#, get_list_or_404
from django.http import QueryDict
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from slam import interface, models
from configuration import RELOAD_SCRIPT

POOL_MAP_LIMIT = 4096

def msg_view(request, title, message, referer=None):
    """View used to display a simple message to the user."""
    tmp_values = {"request": request, "title": title, "msg": message}
    if referer:
        tmp_values["referer"] = referer
    else:
        tmp_values["referer"] = request.META.get("HTTP_REFERER")
    if request.GET.get("format") == "json":
        return render_to_response("message.txt", tmp_values)
    else:
        return render_to_response("message.html", tmp_values)


def error_view(request, status, title, message):
    """View used to display a given error code to the user."""
    tmp_values = {"request": request, "title": title, "msg": message,
        "referer": request.META.get("HTTP_REFERER")}
    if request.GET.get("format") == "json":
        return render(request, "error.txt", tmp_values, status=status)
    else:
        return render(request, "error.html", tmp_values, status=status)


def error_404(request):
    """View rendered when encountering a 404 error."""
    return error_view(request, 404, _("Not found"),
        _("Could not found the resource %(res)s.") % {"res": request.path})


def error_403(request):
    """View rendered when encountering a 403 error."""
    return error_view(request, 403, _("Forbidden"),
        _("You are not allowed to acces to the resource %(res)s.")
            % {"res": request.path})


def error_500(request):
    """View rendered when encountering a 500 error."""
    return error_view(request, 404, _("Internal Error"),
        _("An internal error occured while generating the page for %(res)s.")
            % {"res": request.path})


def request_data(request):
    """Get request body for every request method. Multi-part are *not* handled
    by this function."""
    if request.method == "POST":
        data = request.POST
    if request.method == "GET":
        data = request.GET
    else:
        data = QueryDict(request.raw_post_data)
    return data


@login_required
def logout(request):
    """View use to destroy the user session."""
    auth.logout(request)
    return msg_view(request, _("Disconnected"),
        _("You have successfully been disconnected from SLAM."), referer="/")

@csrf_exempt
def login(request):
    """View used to log into the interface."""
    if request.method == "POST":
        user = auth.authenticate(username=request.POST["username"],
            password=request.POST["password"])
        if user is not None:
            auth.login(request, user)
            return msg_view(request, _("Logged in"),
                _("You can now manage your addresses!"), referer="/")
        else:
            return render_to_response("login.html",
                {"request": request, "error": _("Invalid login or password."),
                    "username": request.POST["username"]})
    else:
        return render_to_response("login.html", {"request": request})


@login_required
def list_pools(request):
    """List available pools in the database."""
    poolobjs = models.Pool.objects.all().order_by("name")
    pools = []
    for poolobj in poolobjs:
        addr_used = models.Address.objects.filter(pool=poolobj).count()
        addr_avail = poolobj.len()
        pools.append((poolobj,
            addr_used, addr_avail, addr_used * 100 / addr_avail))

    if request.GET.get("format") == "json":
        return render_to_response("pool_list.json",
            {"request": request, "pool_list": pools})
    else:
        return render_to_response("pool_list.html",
            {"request": request, "pool_list": pools})


@login_required
def add_pool(request):
    """Create a new pool."""
    if request.method == "POST":
        pool_name = request.POST.get("name")
        try:
            category = request.POST.get("category")
            if category:
                poolobj = interface.create_pool(pool_name,
                    request.POST.get("definition"), [category])
            else:
                poolobj = interface.create_pool(
                    pool_name, request.POST.get("definition"))
        except interface.DuplicateObjectError:
            return error_view(request, 409, _("Pool already exists"),
                _("A pool with the same name or the same category already"
                    " exists in the database."))
        except interface.MissingParameterError:
            return error_view(request, 400, _("Missing information"),
                _("You must specify at least a name and a definition to create"
                    " a new pool."))
        except addrrange.InvalidAddressError:
            return error_view(request, 412, _("Invalid address range"),
                _("The address range you provided is invalid."))
        return msg_view(request,
            _("Created pool %(pool)s") % {"pool": pool_name},
            _("The pool \"%(pool)s\" have been created: %(poolstr)s.")
                % {"pool": pool_name, "poolstr": str(poolobj)},
                referer="/pool/" + str(pool_name))
    else:
        return render_to_response("add_pool.html", {"request": request})

@login_required
def pool_info(request, pool_name):
    """Manipulate a specified pool."""
    data = request_data(request)
    poolobj = get_object_or_404(models.Pool, name=pool_name)
    if request.method == "PUT":
        try:
            category = data.get("category")
            if category:
                interface.modify(pools=[pool_name], category=[category],
                    newname=data.get("newname"))
            else:
                interface.modify(pools=[pool_name],
                    newname=data.get("newname"))
        except interface.MissingParameterError as exc:
            return error_view(request, 400, _("Bad Request"),
                _("Your request is invalid, please verify it is correct. "
                    "Internal reason: %(exc)s") % {"exc": str(exc)})
        except (interface.InexistantObjectError,
                interface.DuplicateObjectError):
            return error_404(request)
        if data.get("newname"):
            referer = "/pool/" + str(data.get("newname"))
        else:
            referer = "/pool/" + pool_name
        return msg_view(request,
            _("Pool \"%(pool)s\" has been modified") % {"pool": pool_name},
            _("The pool \"%(pool)s\" has been correctly modified.")
                % {"pool": pool_name}, referer=referer)
    elif request.method == "DELETE":
        name = str(poolobj.name)
        def_ = str(poolobj)
        try:
            interface.delete(pool=poolobj)
        except interface.InexistantObjectError:
            return error_404(request)
        except models.AddressNotAllocatedError:
            return error_view(request, 412, _("Address not allocated"),
                _("The address you provided is already unallocated."))
        return msg_view(request,
            _("%(name)s has been removed") % {"name": name},
            _("The pool \"%(name)s\" (%(def)s) has been removed.")
                % {"name": name, "def": def_}, referer="/pool")
    else:
        addr_used = models.Address.objects.filter(pool=poolobj).count()
        addr_avail = poolobj.len()
        addrs = models.Address.objects.filter(pool=poolobj)
        if request.GET.get("sort") == "name":
            addrs = addrs.order_by("host__name")
        elif request.GET.get("sort") == "alias":
            addrs = addrs.order_by("host__alias__name")
        elif request.GET.get("sort") == "mac":
            addrs = addrs.order_by("macaddr")
        else:
            addrs = list(addrs)
            addrs = interface.sort_addresses(addrs)
        templ_values = {"request": request,
            "pool": poolobj,
            "addr_used": addr_used,
            "addr_avail": addr_avail,
            "addr_perc": addr_used * 100 / addr_avail,
            "addrs": addrs,
            "props": models.Property.objects.filter(pool=poolobj)}
        if request.GET.get("format") == "json":
            return render_to_response("pool.json", templ_values)
        else:
            return render_to_response("pool.html", templ_values)


@login_required
def pool_map(request, pool_name):
    """Make a map of the allocation of addresses inside a pool."""
    addrs = []
    poolobj = get_object_or_404(models.Pool, name=pool_name)
    poolobj._update()
    addr_used = models.Address.objects.filter(pool=poolobj).count()
    addr_avail = poolobj.len()
    pool_addrs = models.Address.objects.filter(pool=poolobj)
    i = POOL_MAP_LIMIT
    for addr in poolobj.addr_range:
        if i == 0:
            break
        if poolobj.isallocated(addr):
            addrs.append(pool_addrs.get(addr=addr))
        else:
            addrs.append(models.Address(addr=addr, pool=None, host=None))
        i -= 1
    templ_values = {"request": request,
        "pool": poolobj,
        "addrs": addrs,
        "addr_used": addr_used,
        "addr_avail": addr_avail,
        "addr_perc": addr_used * 100 / addr_avail,
        "overflow": addr_avail > POOL_MAP_LIMIT}
    return render_to_response("pool_map.html", templ_values)


@login_required
def list_hosts(request):
    """List all host objects in the database."""
    search = False

    if request.method == "POST":
        search = True
        hosts = models.Host.objects.all()
        if request.POST.get("name"):
            hosts = hosts.filter(name__icontains=request.POST.get("name"))
        if request.POST.get("addr"):
            hosts = hosts.filter(
                address__addr__icontains=request.POST.get("addr"))
        if request.POST.get("macaddr"):
            hosts = hosts.filter(
                address__macaddr__icontains=request.POST.get("macaddr"))
        if request.POST.get("alias"):
            hosts = hosts.filter(
                alias__name__icontains=request.POST.get("alias"))
        if request.POST.get("inventory"):
            hosts = hosts.filter(
                inventory__icontains=request.POST.get("inventory"))
        if request.POST.get("serial"):
            hosts = hosts.filter(serial__icontains=request.POST.get("serial"))
        if request.POST.get("owner"):
            hosts = hosts.filter(
                property__value__icontains=request.POST.get("owner"))
    else:
        hosts = models.Host.objects.all()
        if request.GET.get("sort") == "addr":
            hosts = hosts.order_by("address__addr")
        elif request.GET.get("sort") == "alias":
            hosts = hosts.order_by( "alias__name")
        elif request.GET.get("sort") == "mac":
            hosts = hosts.order_by("address__macaddr")
        else:
            hosts = hosts.order_by("name")

    host_list = []
    for host in hosts:
        addrs = models.Address.objects.filter(host=host).order_by("addr")
        host_list.append((host, addrs))

    context_values = {"request": request, "host_list": host_list,
        "search": search}
    if request.GET.get("format") == "json":
        return render_to_response("host_list.json", context_values)
    else:
        return render_to_response("host_list.html", context_values)


@login_required
def search_hosts(request):
    """Allow to search the host list for a specific host."""
    return render_to_response("host_search.html", {"request": request})


@login_required
def add_host(request):
    """Add a new host to SLAM's database."""
    if request.method == "POST":
        try:
            pool = interface.get_pool(pool_name=request.POST.get("pool_name"),
                category=request.POST.get("category"))
        except interface.InexistantObjectError:
            return error_404(request)
        alias = request.POST.get("alias")
        if alias:
            alias = alias.replace(", ", ",").split(",")
        else:
            alias = []
        if (request.POST.get("mac") and models.Address.objects.filter(
                macaddr=request.POST.get("mac"))):
            return error_view(request, 412, _("MAC adress taken"),
                _("The MAC adresse of the host you are trying to create "
                    "already belongs to host %(host)s.")
                    % {"host": models.Address.objects.filter(
                            macaddr=request.POST.get("mac"))[0].host.name})

        mac = request.POST.get("mac")
        if mac:
            mac = mac.lower()
            if not re.match("^[a-f0-9]{2}(:[a-f0-9]{2}){5}$", mac):
                return error_view(request, 400, _("Invalid MAC"),
                    _("The format of the given MAC address is invalid :"
                        " %(mac)s.") % {"mac": mac})
        try:
            hoststr, addrstr = interface.create_host(
                host=request.POST.get("name"),
                pool=pool,
                address=request.POST.get("address"),
                mac=mac,
                random=request.POST.get("random"),
                alias=alias,
                serial=request.POST.get("serial"),
                inventory=request.POST.get("inventory"),
                nodns=request.POST.get("nodns"))
        except interface.MissingParameterError:
            return error_view(request, 400, _("Missing information"),
                _("You must at least specify a name to create a new host."))
        #annomalie espace dans le name host
        except interface.PropertyFormatError:
            return error_view(request, 400, _("Format invalid"),
                _("You must specify a valid host name or alias without space, special character etc."))
        #anomalie9
        except interface.DuplicateObjectError, e:
            return error_view(request, 409, _("Could not create host"), e.args[0])
        #fin anomalie9
        except models.AddressNotInPoolError:
            return error_view(request, 412, _("Address not in pool"),
                _("The address you provided (%(addr)s) is not in the pool "
                    "%(pool)s.")
                    % {"addr": str(request.POST.get("address")),
                        "pool": str(pool.name)})
        except models.AddressNotAvailableError:
            return error_view(request, 412, _("Address not available"),
                _("The address you asked for (%(addr)s) is not available.")
                    % {"addr": str(request.POST.get("address"))})
        except models.FullPoolError:
            return error_view(request, 412, _("Pool is full"),
                _("The destination address pool (%(pool)s) is full. "
                    "Impossible to allocate another IP in this pool.")
                    % {"pool": str(pool.name)})
        msg = _("The host \"%(host)s\" have been created") % {"host": hoststr}
        if addrstr:
            msg = msg + _(" and was assigned to address: ") + addrstr
        if request.POST.get("owner"):
            try:
                interface.set_prop("owner", request.POST.get("owner"),
                    host=request.POST.get("name"))
            except interface.InexistantObjectError:
                error_404(request)
            except interface.MissingParameterError:
                return error_view(request, 400, _("Missing information"),
                    _("You must at least specify the name of the new property "
                        "you want to create."))
        return msg_view(request,
            _("Created host %(host)s") % {"host": hoststr}, msg,
            referer="/host/" + hoststr)
    else:
        categories = []
        for pools in models.Pool.objects.exclude(category=""):
            for cat in pools.category.split(","):
                if cat not in categories:
                    categories.append(cat)
        context_values = {"request": request,
            "pools": [pool.name for pool in
                models.Pool.objects.all().order_by("name")],
            "categories": sorted(categories)}
        return render_to_response("add_host.html", context_values)


@login_required
def host_info(request, host_name):
    """Manipulate or show a host in the database."""
    data = request_data(request)
    try:
        host = interface.get_host(host_name)
    except interface.InexistantObjectError:
        return error_404(request)

    if request.method == "PUT":
        category = data.get("category")
        if category:
            category = [category]
        alias = data.get("alias")
        if not alias:
            alias = ""
        alias = alias.replace(", ", ",")
        if alias:
            alias = alias.split(",")
        mac = data.get("macaddr")
        try:
            if mac:
                mac = mac.lower()
                if not re.match("^[a-f0-9]{2}(:[a-f0-9]{2}){5}$", mac):
                    return error_view(request, 400, _("Invalid MAC"),
                        _("The format of the given MAC address is invalid :"
                            " %(mac)s.") % {"mac": mac})

            interface.modify(host=host_name,
                mac=data.get("macaddr"),
                newname=data.get("newname"),
                category=category,
                alias=alias,
                serial=data.get("serial"),
                inventory=data.get("inventory"),
                nodns=((data.get("nodns") == "on") != host.nodns),
                clearalias=data.get("clearalias") == "on")
            if data.get("owner"):
                interface.set_prop("owner", data.get("owner"), host=host)
        except interface.MissingParameterError:
            return error_view(request, 400, _("Missing information"),
                _("You must specify the new values to modify an object."))
        #annomalie espace dans le name host
        except interface.PropertyFormatError:
            return error_view(request, 400, _("Format invalid"),
                _("You must specify a valid host name or alias without space, special character etc."))
        #anomalie9
        except interface.DuplicateObjectError, e:
            return error_view(request, 409, _("Host or alias already exists"), e.args[0])
        #fin anomalie9
        except interface.InexistantObjectError:
            return error_404(request)
        if data.get("newname"):
            referer = "/host/" + str(data.get("newname"))
        else:
            referer = "/host/" + host_name
        return msg_view(request,
            _("Host \"%(host)s\" has been modified") % {"host": host_name},
            _("The host \"%(host)s\" has been correctly modified.")
                    % {"host": host_name}, referer=referer)
    elif request.method == "POST" and request.POST.get("allocate"):
        poolobj = None
        if request.POST.get("pool_name"):
            poolobj = interface.get_pool(request.POST.get("pool_name"))
        try:
            addr = interface.allocate_address(
                pool=poolobj,
                host=host, address=request.POST.get("address"),
                category=host.category)
        except interface.MissingParameterError:
            return error_view(request, 400, _("Missing information"),
                _("Host probably does not have a category, please add one to "
                    " it or specify a pool or an address in the previous form."))
        except models.AddressNotInPoolError:
            return error_view(request, 412, _("Address not in the given pool"),
                _("The address you provided (%(addr)s) does not belong to the "
                    "given pool."))
        except models.AddressNotAvailableError:
            return error_view(request, 412, _("Address not available."),
                _("The address you provided is already allocated. Impossible "
                    "to reallocate it to this host."))

        return msg_view(request, _("Allocated %(addr)s") % {"addr": addr.addr},
            _("The address %(addr)s has correctly been allocated to host "
                "%(host)s.") % {"addr": addr.addr, "host": host.name})
    else:
        addrs = models.Address.objects.filter(host=host).order_by("addr")
        if request.method == "DELETE":
            if data.get("confirm"):
                return render_to_response("host.html", {"request": request,
                    "host": host, "addrs": addrs, "confirm_delete": 1})
            else:
                get_object_or_404(models.Host, name=host_name)
                try:
                    interface.delete(hosts=[host_name])
                except interface.InexistantObjectError:
                    return error_404(request)
                return msg_view(request, host_name + _(" has been removed"),
                    _("The host \"%(host)s\" has correctly been removed.")
                        % {"host": host_name}, referer="/host")
        else:
            tmp_val = {"request": request, "host": host, "addrs": addrs,
                "pools": models.Pool.objects.all(),
                "mac": ", ".join([addr.macaddr for addr in addrs]),
                "props": models.Property.objects.filter(host=host)}
            if models.Property.objects.filter(name="owner", host=host):
                tmp_val["owner"] = models.Property.objects.get(
                    name="owner", host=host).value
            if request.GET.get("format") == "json":
                return render_to_response("host.json", tmp_val)
            else:
                return render_to_response("host.html", tmp_val)


@login_required
def address_info(request, address):
    """Get information about an address or disallocate it."""
    addr = get_object_or_404(models.Address, addr=address)
    if request.method == "POST":
        try:
            interface.modify(address=address,
                comment=request.POST.get("comment"),
                duration=int(request.POST.get("duration")))
        except interface.InexistantObjectError:
            return error_view(request, 400, _("Missing information"),
                _("You must specify at least the comment or duration to "
                    "modify."))
        return msg_view(request, _("Address modified"),
            _("The address \"%(addr)s\" has been correctly modified.")
                % {"addr": address}, referer="/address/" + address)
    if request.method == "DELETE":
        data = request_data(request)
        if data.get("confirm"):
            return render_to_response("address.html",
                {"request": request, "addr": addr, "confirm_delete": 1})
        else:
            try:
                interface.delete(addresses=[address])
            except interface.InexistantObjectError:
                error_404(request)
            return msg_view(request, _("Address deleted"),
                _("The address \"%(addr)s\" has been correctly removed.")
                    % {"addr": address}, referer="/")
    else:
        if request.GET.get("format") == "json":
            return render_to_response("address.json",
                {"request": request, "addr": addr})
        else:
            return render_to_response("address.html",
                {"request": request, "addr": addr})


@login_required
def list_logs(request):
    """List all log for the service."""
    data = request_data(request)
    if request.method == "DELETE" and data.get("days"):
        interface.delete_logs(days=int(data.get("days")))

    msgs = [str(entry) for entry
        in models.LogEntry.objects.all().order_by("date")]

    if request.GET.get("format") == "json":
        return render_to_response("logs.json",
            {"request": request, "msgs": msgs})
    else:
        return render_to_response("logs.html",
            {"request": request, "msgs": msgs})


@login_required
def property_(request):
    """Create, edit or delete a property."""
    if request.method == "POST" or request.method == "DELETE":
        try:
            interface.set_prop(request.POST.get("name"),
                request.POST.get("value"), request.POST.get("pool"),
                request.POST.get("host"), request.method == "DELETE")
        except interface.MissingParameterError():
            return error_view(request, 400, _("Missing information"),
                _("You must at least specify a pool or a host and the name of"
                    " property to create, edit or delete a property."))
        except interface.InexistantObjectError:
            return error_404(request)
        #except interface.inexistant
        if request.POST.get("host"):
            return redirect("/host/" + request.POST.get("host"))
        elif request.POST.get("pool"):
            return redirect("/host/" + request.POST.get("pool"))

    return redirect("/")


@login_required
def reload(request):
    """Generate all configuration files."""
    if request.method == "POST":
        if RELOAD_SCRIPT and os.access(RELOAD_SCRIPT, os.X_OK):
            proc = subprocess.Popen(["/bin/sh", RELOAD_SCRIPT],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout = proc.stdout.read()
            stderr = proc.stderr.read()
            ret = proc.wait()
            return render_to_response("reload.html",
                {"request": request, "executed": True,
                    "error": ret != 0, "stdout": stdout, "stderr": stderr})
        else:
            return error_view(request, 500, _("Could not generate files"),
                _("Impossible to generate configuration files, the "
                    "RELOAD_SCRIPT variable is not defined in the SLAM's "
                    "configuration file."))
    else:
        return render_to_response("reload.html", {"request": request})


def lang(request):
    """View that allow interface's language switching."""
    return render_to_response("lang.html",
        {"request": request, "avail_lang": ["en", "fr"],
            "referer": request.META["HTTP_REFERER"]}, RequestContext(request))
