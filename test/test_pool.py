"""
Test module for the pool class in SLAM.
"""

from nose.tools import assert_raises

from slam import addrrange, models


def test_pool():
    ipr = addrrange.Ip4Range("192.168.0.0/24")
    p = models.Pool.create("localnet1", ipr)
    assert p.name == "localnet1"
    assert len(p.addr_range) == 2 ** 8
    assert str(p.addr_range) == "192.168.0.0/24"

    p = models.Pool.create("setnet1", definition="addr1,addr2,addr3")
    p.save()
    p = models.Pool.objects.get(name="setnet1")
    p._update()
    assert p.addr_range.addr_set == set(["addr1", "addr2", "addr3"])

    ips = models.Pool.create(definition="")
    assert ips.addr_range_type == "set"


def test_pool_get():
    p = models.Pool.create("localnet10", definition="192.168.10.0/24")
    p.save()
    assert str(p.get()) == "192.168.10.0"
    assert str(p.get()) == "192.168.10.1"
    for i in range(50):
        p.get()
    assert str(p.get()) == "192.168.10.52"
    assert models.Address.objects.filter(allocated=True, pool=p).count() == 53

    p = models.Pool.create("localnet12", definition="fe80::/13")
    p.save()
    assert str(p.get()) == "fe80:0000:0000:0000:0000:0000:0000:0000"
    assert str(p.get()) == "fe80:0000:0000:0000:0000:0000:0000:0001"
    for i in range(50):
        p.get()
    assert str(p.get()) == "fe80:0000:0000:0000:0000:0000:0000:0034"
    assert models.Address.objects.filter(allocated=True, pool=p).count() == 53

    fruitset = set(["apple", "orange", "peach", "pear"])
    p = models.Pool.create("localnet13", definition="apple,orange,peach,pear")
    p.save()
    assert str(p.get()) in fruitset
    assert str(p.get()) in fruitset
    assert str(p.get()) in fruitset
    assert str(p.get()) in fruitset
    assert_raises(models.FullPoolError, p.get)


def test_pool_get_rand():
    p = models.Pool.create("localnet15", definition="192.168.15.0/24")
    p.save()
    assert str(p.get_rand()) in p.addr_range
    assert str(p.get_rand()) in p.addr_range
    assert str(p.get_rand()) in p.addr_range

    p = models.Pool.create("localnet17", definition="fe80::/13")
    p.save()
    assert str(p.get_rand()) in p.addr_range
    assert str(p.get_rand()) in p.addr_range
    assert str(p.get_rand()) in p.addr_range

    p = models.Pool.create("localnet18", definition="apple,orange,peach,pear")
    p.save()
    assert str(p.get_rand()) in p.addr_range
    p.get()
    p.get()
    p.get()
    assert_raises(models.FullPoolError, p.get_rand)


def test_pool_allocate():
    p = models.Pool.create("localnet20", definition="192.168.20.0/24")
    p.save()
    assert str(p.get()) == "192.168.20.0"
    p.allocate("192.168.20.1")
    assert str(p.get()) == "192.168.20.2"

    p = models.Pool.create("localnet22", definition="fe80::/13")
    p.save()
    assert str(p.get()) == "fe80:0000:0000:0000:0000:0000:0000:0000"
    p.allocate("fe80:0000:0000:0000:0000:0000:0000:0001")
    assert str(p.get()) == "fe80:0000:0000:0000:0000:0000:0000:0002"

    fruitset = set(["apple", "orange", "peach"])
    p = models.Pool.create("localnet23", definition="apple,orange,peach,pear")
    p.save()
    p.allocate("pear")
    assert str(p.get()) in fruitset
    assert str(p.get()) in fruitset
    assert str(p.get()) in fruitset


def test_pool_free():
    p = models.Pool.create("localnet30", definition="192.168.30.0/24")
    p.save()
    addr = p.get()
    p.get()
    p.free(str(addr.addr))
    assert str(p.get()) == str(addr)

    p = models.Pool.create("localnet32", definition="fe80::/13")
    p.save()
    addr = p.get()
    p.get()
    p.free(str(addr.addr))
    assert str(p.get()) == str(addr)

    p = models.Pool.create("localnet33", definition="apple,orange,peach,pear")
    p.save()
    addr = p.get()
    p.get()
    p.free(str(addr.addr))
    assert str(p.get()) == str(addr)


def test_isallocated():
    p = models.Pool.create("localnet35", definition="192.168.35.0/24")
    p.save()
    assert not p.isallocated("192.168.35.0")
    assert not p.isallocated("192.168.35.255")
    assert str(p.get()) == "192.168.35.0"
    assert p.isallocated("192.168.35.0")
    assert not p.isallocated("192.168.35.23")
    p.allocate("192.168.35.23")
    assert p.isallocated("192.168.35.23")
    p.free("192.168.35.23")
    assert not p.isallocated("192.168.35.23")
    assert_raises(models.AddressNotInPoolError, p.isallocated, "10.9.8.7")


def test_pool_full():
    p = models.Pool.create("tinynet", definition="192.168.50.0/30")
    p.save()
    p.allocate("192.168.50.0")
    p.allocate("192.168.50.3")
    p.get()
    p.get()
    assert_raises(models.FullPoolError, p.get)

def test_pool_contains():
    p = models.Pool.create("localnet55", definition="192.168.55.0/24")
    p.save()
    p.get()
    assert "192.168.55.0" in p
    assert "192.168.55.1" in p
    assert "192.168.56.1" not in p

def test_addr_not_in_pool():
    p = models.Pool.create("localnet60", definition="192.168.60.0/24")
    p.save()
    assert_raises(models.AddressNotInPoolError, p.allocate, "192.168.7.0")
    assert_raises(models.AddressNotInPoolError, p.free, "192.168.7.0")
    p.allocate("192.168.60.0")
    p.allocate("192.168.60.255")
    assert_raises(models.AddressNotInPoolError, p.allocate, "192.168.5.255")
    assert_raises(models.AddressNotInPoolError, p.free, "192.168.5.255")


def test_addr_not_available():
    p = models.Pool.create("localnet70", definition="192.168.70.0/24")
    p.save()
    assert str(p.get()) == "192.168.70.0"
    p.allocate("192.168.70.1")
    assert_raises(models.AddressNotAvailableError, p.allocate, "192.168.70.0")


def test_addr_not_allocated():
    p = models.Pool.create("localnet80", definition="192.168.80.0/24")
    p.save()
    assert_raises(models.AddressNotAllocatedError, p.free, "192.168.80.0")
    assert str(p.get()) == "192.168.80.0"
    p.free("192.168.80.0")
    assert_raises(models.AddressNotAllocatedError, p.free, "192.168.80.0")
    assert_raises(models.AddressNotAllocatedError, p.free, "192.168.80.42")
