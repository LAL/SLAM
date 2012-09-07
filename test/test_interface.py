"""Test module for the generic interface."""

import os, tempfile
from nose.tools import assert_raises

from slam.models import Pool, Host, Address, Property
from slam import interface, generator

def test_getcreate_host():
    interface.create_host(host="host10")

    hostobj = interface.get_host("host10")
    assert str(hostobj) == "host10"

    assert interface.get_host(None) is None
    assert_raises(interface.InexistantObjectError,
        interface.get_host, "inexistant")

    interface.create_pool("pool10", "10.10.0.0/24", ["cat10"])
    interface.create_host(host="host10-2", pool=interface.get_pool("pool10"))
    assert(interface.get_host("host10-2").address_set.all()[0].pool.name
        == "pool10")
    interface.create_host(host="host10-3",
        pool=interface.get_pool(category="cat10"))
    assert(interface.get_host("host10-3").address_set.all()[0].pool.name
        == "pool10")
    assert_raises(interface.DuplicateObjectError, interface.create_host,
        "host10-3")

    interface.create_host(host="host10-4", mac="mac10-4", category="cat10")
    assert(interface.get_host("host10-4").category == "cat10")
    assert(Address.objects.get(host__name="host10-4").pool.name == "pool10")
    assert(interface.get_host("host10-4").address_set.all()[0].macaddr
        == "mac10-4")

    interface.create_host(host="host10-6",
        pool=Pool.objects.get(name="pool10"), address="10.10.0.142")
    assert Address.objects.get(host__name="host10-6").addr == "10.10.0.142"

    interface.create_host(host="host10-5", pool=interface.get_pool("pool10"),
        mac="mac10-5")
    addrobj = interface.get_host("host10-5").address_set.all()[0]
    assert addrobj.addr == "10.10.0.3" and addrobj.macaddr == "mac10-5"

    interface.create_host(host="host10-15", pool=interface.get_pool("pool10"),
        alias=["alias10-1", "alias10-2"])
    hostobj = interface.get_host("host10-15")
    assert(len(hostobj.alias_set.all()) == 2 and
        hostobj.alias_set.all()[1].name == "alias10-2")

    interface.create_pool("pool10-2", "172.16.102.0/24", ["cat10"])
    interface.create_host(host="host10-25", address="172.16.102.234")
    assert(Address.objects.get(host__name="host10-25").pool.name == "pool10-2")


def test_macaddress():
    interface.create_pool("pool15", "10.15.0.0/24")
    interface.create_host(host="host15-1")
    assert not Address.objects.filter(host__name="host15-1")

    interface.create_host("host15-2", pool=interface.get_pool("pool15"),
        mac="mac-2")
    assert Address.objects.get(host__name="host15-2").macaddr == "mac-2"

    interface.create_host("host15-3", mac="mac-3")
    assert Address.objects.get(host__name="host15-3").macaddr == "mac-3"

    interface.create_host("host15-4", pool=interface.get_pool("pool15"),
        mac="mac-4", address="10.15.0.142")
    assert Address.objects.get(host__name="host15-4").macaddr == "mac-4"


def test_getcreate_pool():
    interface.create_pool("pool20", "10.20.0.0/24", ["cat20"])
    assert(str(interface.get_pool(pool_name="pool20"))
        == "pool20 (range: 10.20.0.0/24)")
    assert interface.get_pool(category="cat20").name == "pool20"

    interface.create_pool("pool20-2", "10.20.2.0/24")
    assert(str(interface.get_pool(pool_name="pool20-2"))
        == "pool20-2 (range: 10.20.2.0/24)")

    assert_raises(interface.InexistantObjectError,
        interface.get_pool, "inexistant")
    assert_raises(interface.InexistantObjectError,
        interface.get_pool, None, "inexistant")

    assert_raises(interface.DuplicateObjectError,
        interface.create_pool, "pool20-2", "10.20.3.0/24")
    assert_raises(interface.MissingParameterError,
        interface.create_pool, "pool20-3")


def test_modify():
    interface.create_pool("pool30-1", "10.30.1.0/24")

    assert interface.get_pool("pool30-1").category == ""
    interface.modify(["pool30-1"], category=["cat30-1"])
    assert interface.get_pool("pool30-1").category == "cat30-1"
    interface.modify(["pool30-1"], newname="pool30-2")
    assert(Pool.objects.filter(name="pool30-2")
        and interface.get_pool("pool30-2").category == "cat30-1")

    interface.create_host(host="host30-1", pool=interface.get_pool("pool30-2"),
        mac="foobar")
    assert Address.objects.get(host__name="host30-1").macaddr == "foobar"
    interface.modify(host="host30-1", mac="mac30-1")
    assert Address.objects.get(host__name="host30-1").macaddr == "mac30-1"
    interface.modify(host="host30-1", newname="host30-2")
    assert(Host.objects.filter(name="host30-2")
        and Address.objects.get(host__name="host30-2").macaddr == "mac30-1")
    hostobj = interface.get_host("host30-2")
    assert len(hostobj.alias_set.all()) == 0
    interface.modify(host="host30-2", alias=["alias30-1", "alias30-2"])
    assert(len(hostobj.alias_set.all()) == 2
        and hostobj.alias_set.all()[1].name == "alias30-2")

    assert_raises(interface.MissingParameterError,
        interface.modify, ["pool30-2"])
    assert_raises(interface.MissingParameterError,
        interface.modify, None, "host30-2")
    assert_raises(interface.InexistantObjectError, interface.modify, None)

    interface.create_host(host="host30-3", pool=interface.get_pool("pool30-2"),
        address="10.30.1.142", mac="foobar")
    interface.modify(host="host30-3", address="10.30.1.142", mac="barfoo")
    assert Address.objects.get(host__name="host30-3").macaddr == "barfoo"

    interface.create_host(host="host30-4")
    interface.modify(host="host30-4", mac="imac")
    assert Address.objects.get(host__name="host30-4").macaddr == "imac"


def test_getcreate_generator():
    interface.create_generator("rdnsgen", "revbind", "-", timeout="5H")
    gen = interface.get_generator("rdnsgen")
    assert gen.type_ == "rbind" and gen.timeout == "5H" and not gen.default

    interface.create_generator("dhcpgen", "dhcp", "-", True)
    gen = interface.get_generator("dhcpgen")
    assert gen.type_ == "dhcp" and gen.default
    interface.modify_generator("dhcpgen", True)
    gen = interface.get_generator("dhcpgen")
    assert not gen.default
    interface.modify_generator("dhcpgen", True)
    gen = interface.get_generator("dhcpgen")
    assert gen.default
    gen = interface.get_default_generators()
    assert gen[0].name == "dhcpgen"
    gen = interface.get_default_generators("dns")
    assert len(gen) == 0

    interface.create_generator("quattgen", "quattor", "-")
    gen = interface.get_generator("quattgen")
    assert gen.type_ == "quatt"

    interface.create_generator("dnsgen", "bind", "-", timeout="6H")
    gen = interface.get_generator("dnsgen")
    assert gen.type_ == "bind" and gen.timeout == "6H"
    gen.save()
    gen = generator.BindConfig.objects.get(name="dnsgen")
    assert(gen.outputfile == "-" and not gen.headerfile and not gen.footerfile
        and not gen.checkfile and gen.timeout == "6H" and not gen.domain)
    interface.modify_generator("dnsgen", False, "./random.conf", "headerf",
        "footerf", ["checkf", "checkf2"], "8H", "test.example")
    gen = generator.BindConfig.objects.get(name="dnsgen")
    assert(gen.outputfile == "./random.conf" and gen.headerfile == "headerf"
        and gen.footerfile == "footerf" and gen.checkfile == "checkf, checkf2"
        and gen.timeout == "8H" and gen.domain == "test.example")

    assert_raises(interface.DuplicateObjectError,
        interface.create_generator, "dnsgen", "bind", "-")
    assert_raises(interface.MissingParameterError,
        interface.create_generator, None, "bind", None)
    assert_raises(interface.MissingParameterError,
        interface.create_generator, "randgen", "inexistant", "-")
    assert_raises(interface.InexistantObjectError,
        interface.get_generator, "inexistant")


def test_generate():
    # most of the test are in test_generator.py
    interface.create_pool("pool40", "10.40.0.0/24")
    interface.create_host(host="host40-1", pool=interface.get_pool("pool40"))
    interface.create_host(host="host40-2", pool=interface.get_pool("pool40"))

    interface.generate(None, ["pool40"], "bind", "-", update=False)
    assert_raises(interface.ConfigurationFormatError, interface.generate, None,
        ["pool40"], "unknown", "-", None, None, False)

    handle, path = tempfile.mkstemp()
    interface.create_generator("dnsgen2", "bind", path, timeout="6H")
    interface.generate("dnsgen2", ["pool40"], output="-", update=False)
    f = open(path, "r+")
    res = f.read()
    assert(res == "\n; This section will be automatically generated by SLAM"
        + " any manual change will\n; be overwritten on the next generation of"
        + " this file.\n"
        + "host40-1\t6H\tIN\tA\t10.40.0.0\n"
        + "host40-2\t6H\tIN\tA\t10.40.0.1\n"
        + "; END of section automatically generated by SLAM\n")

    f.close()
    os.unlink(path)


def test_delete():
    interface.create_pool("pool50", "10.50.0.0/24")
    interface.create_host(host="host50-1", pool=interface.get_pool("pool50"))
    interface.create_host(host="host50-2", pool=interface.get_pool("pool50"))
    interface.create_host(host="host50-3", pool=interface.get_pool("pool50"))
    Pool.objects.get(name="pool50").allocate("10.50.0.42",
        Host.objects.get(name="host50-3"))

    assert Host.objects.filter(name="host50-1")
    interface.delete(hosts=["host50-1"])
    assert not Host.objects.filter(name="host50-1")
    assert not Address.objects.filter(addr="10.50.0.0")

    assert Address.objects.filter(host__name="host50-3").count() == 2
    interface.delete(addresses=["10.50.0.42"])
    assert Address.objects.filter(host__name="host50-3").count() == 1

    assert Pool.objects.filter(name="pool50")
    interface.delete(pool=Pool.objects.get(name="pool50"))
    assert not Pool.objects.filter(name="pool50")
    assert not Address.objects.filter(host__name="host50-2")

    assert_raises(interface.InexistantObjectError, interface.delete, None,
        ["inexistant"])


def test_prop():
    interface.create_pool("pool60", "10.60.0.0/24")
    interface.create_host(host="host60-1", pool=interface.get_pool("pool60"))

    interface.quick_set_prop("prop=value", "pool60")
    assert(Property.objects.get(
        pool__name="pool60", name="prop").value == "value")
    interface.quick_set_prop("prop2=value2", host="host60-1")
    assert(Property.objects.get(
        host__name="host60-1", name="prop2").value == "value2")

    interface.quick_set_prop("prop", "pool60", del_=True)
    assert not Property.objects.filter(pool__name="pool60")
    interface.quick_set_prop("prop2", host="host60-1", del_=True)
    assert not Property.objects.filter(host__name="host60-1")

    assert_raises(interface.PropertyFormatError, interface.quick_set_prop,
        "foobar", "pool60")
    assert_raises(interface.InexistantObjectError, interface.quick_set_prop,
        "inexistant", "pool60", del_=True)
