"""Webinterface view functions."""

from django.shortcuts import render_to_response, render, redirect
from django.shortcuts import get_object_or_404#, get_list_or_404
from django.http import QueryDict
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.contrib import auth
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from slam import interface, models

def msg_view(request, title, message):
    """View used to display a simple message to the user."""
    tmp_values = {"request": request, "title": title, "msg": message,
        "referer": request.META.get("HTTP_REFERER")}
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
        _("You have successfully been disconnected from SLAM."))

@csrf_exempt
def login(request):
    """View used to log into the interface."""
    if request.method == "POST":
        user = auth.authenticate(username=request.POST["username"],
            password=request.POST["password"])
        if user is not None:
            auth.login(request, user)
            return msg_view(request, _("Logged in"),
                _("You can now manage your addresses!"))
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
        return msg_view(request,
            _("Created pool %(pool)s") % {"pool": pool_name},
            _("The pool \"%(pool)s\" have been created: %(poolstr)s.")
                % {"pool": pool_name, "poolstr": str(poolobj)})
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
        return msg_view(request,
            _("Pool \"%(pool)s\" has been modified") % {"pool": pool_name},
            _("The pool \"%(pool)s\" has been correctly modified.")
                % {"pool": pool_name})
    elif request.method == "DELETE":
        name = str(poolobj.name)
        def_ = str(poolobj)
        try:
            interface.delete(pool=poolobj)
        except interface.InexistantObjectError:
            return error_404(request)
        return msg_view(request,
            _("%(name)s has been removed") % {"name": name},
            _("The pool \"%(name)s\" (%(def)s) has been removed.")
                % {"name": name, "def": def_})
    else:
        addr_used = models.Address.objects.filter(pool=poolobj).count()
        addr_avail = poolobj.len()
        addrs = list(models.Address.objects.filter(pool=poolobj))
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
    for addr in poolobj.addr_range:
        if poolobj.isallocated(addr):
            addrs.append(pool_addrs.get(addr=addr))
        else:
            addrs.append(models.Address(addr=addr, pool=None, host=None))
    templ_values = {"request": request,
        "pool": poolobj,
        "addrs": addrs,
        "addr_used": addr_used,
        "addr_avail": addr_avail,
        "addr_perc": addr_used * 100 / addr_avail}
    return render_to_response("pool_map.html", templ_values)


@login_required
def list_hosts(request):
    """List all host objects in the database."""
    hosts = models.Host.objects.all().order_by("name")
    host_list = []
    for host in hosts:
        addrs = models.Address.objects.filter(host=host).order_by("addr")
        host_list.append((host, addrs))
    context_values = {"request": request, "host_list": host_list}
    if request.GET.get("format") == "json":
        return render_to_response("host_list.json", context_values)
    else:
        return render_to_response("host_list.html", context_values)


@login_required
def add_host(request):
    """Add a new host to SLAM's database."""
    if request.method == "POST":
        try:
            pool = interface.get_pool(pool_name=request.POST.get("pool_name"),
                category=request.POST.get("category"))
        except interface.InexistantObjectError:
            return error_404(request)
        try:
            hoststr, addrstr = interface.create_host(
                host=request.POST.get("name"),
                pool=pool,
                address=request.POST.get("address"),
                mac=request.POST.get("mac"),
                random=request.POST.get("random"))
        except interface.MissingParameterError:
            return error_view(request, 400, _("Missing information"),
                _("You must at least specify a name to create a new host."))
        except interface.DuplicateObjectError:
            return error_view(request, 409, _("Host already exists"),
                _("Could not create host %(host)s because it already exists.")
                    % {"host": str(request.POST.get("name"))})
        msg = _("The host \"%(host)s\" have been created") % {"host": hoststr}
        if addrstr:
            msg = msg + _(" and was assigned to address: ") + addrstr
        return msg_view(request,
            _("Created host %(host)s") % {"host": hoststr}, msg)
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
    if request.method == "PUT":
        try:
            category = data.get("category")
            if category:
                interface.modify(host=host_name, mac=data.get("macaddr"),
                    newname=data.get("newname"), category=[category])
            else:
                interface.modify(host=host_name, mac=data.get("macaddr"),
                    newname=data.get("newname"))
        except interface.MissingParameterError:
            return error_view(request, 400, _("Missing information"),
                _("You must specify the new values to modify an object."))
        except (interface.InexistantObjectError,
                interface.DuplicateObjectError):
            return error_404(request)
        return msg_view(request,
            _("Host \"%(host)s\" has been modified") % {"host": host_name},
            _("The host \"%(host)s\" has been correctly modified.")
                    % {"host": host_name})
    else:
        host = get_object_or_404(models.Host, name=host_name)
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
                        % {"host": host_name})
        else:
            if request.GET.get("format") == "json":
                return render_to_response("host.json",
                    {"request": request, "host": host, "addrs": addrs})
            else:
                return render_to_response("host.html",
                    {"request": request, "host": host, "addrs": addrs})


@login_required
def address_info(request, address):
    """Get information about an address or disallocate it."""
    addr = get_object_or_404(models.Address, addr=address)
    if request.method == "DELETE":
        interface.delete(addresses=[address])
        return msg_view(request, _("Address deleted"),
            _("The address \"%(addr)s\" has been correctly removed.")
                % {"addr": address})
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
        if request.method == "POST":
            return msg_view(request, _("Property modified"),
                _("The property %(prop)s has been correctly added or edited.")
                    % {"prop": request.POST.get("name")})
        else:
            return msg_view(request, _("Property deleted"),
                _("The property %(prop)s has been correctly deleted.")
                    % {"prop": request.POST.get("name")})
    else:
        return redirect("/")


def lang(request):
    """View that allow interface's language switching."""
    return render_to_response("lang.html",
        {"request": request, "avail_lang": ["en", "fr"],
            "referer": request.META["HTTP_REFERER"]}, RequestContext(request))
