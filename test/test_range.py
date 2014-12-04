"""
Test module for the various provided Adress ranges in SLAM.
"""

import sys
sys.path.append("../src")

from nose.tools import assert_raises

from slam import addrrange
from slam.addrrange import InvalidAddressError

def test_format_ip4():
    assert addrrange._format_ip4(42) == "0.0.0.42"
    assert addrrange._format_ip4(16974599) == "1.3.3.7"
    assert addrrange._format_ip4(3232300823) == "192.168.255.23"


def test_parse_ip4():
    assert addrrange._parse_ip4("0.0.0.42") == 42
    assert addrrange._parse_ip4("1.3.3.7") == 16974599
    assert addrrange._parse_ip4("192.168.255.23") == 3232300823
    assert_raises(InvalidAddressError, addrrange._parse_ip4, "invalid")
    assert_raises(InvalidAddressError, addrrange._parse_ip4, "192.168.256.0")


def test_ip4range():
    ipr = addrrange.Ip4Range("172.16.50.80/12")
    assert addrrange._format_ip4(ipr.net) == "172.16.0.0" and ipr.mask == 12
    ipr = addrrange.Ip4Range("10.42.137.23/28")
    assert addrrange._format_ip4(ipr.net) == "10.42.137.16" and ipr.mask == 28
    assert_raises(InvalidAddressError, addrrange.Ip4Range, "1.2.3.4")
    assert_raises(InvalidAddressError, addrrange.Ip4Range, "1.2.3.4/42")
    assert_raises(InvalidAddressError, addrrange.Ip4Range, "1.23.4/23")

    assert ipr[15] == "10.42.137.31"
    assert_raises(IndexError, ipr.__getitem__, 16)


def test_ip4range_contains():
    ipr = addrrange.Ip4Range("10.42.137.23/28")
    assert "10.42.137.15" not in ipr
    assert "10.42.137.16" in ipr
    assert "10.42.137.23" in ipr
    assert "10.42.137.31" in ipr
    assert "10.42.137.32" not in ipr


def test_ip4range_str():
    ipr = addrrange.Ip4Range("10.42.137.23/28")
    assert str(ipr) == "10.42.137.16/28"
    ipr = addrrange.Ip4Range("172.16.50.80/12")
    assert str(ipr) == "172.16.0.0/12"


def test_format_ip6():
    assert(addrrange._format_ip6(42) ==
        "0000:0000:0000:0000:0000:0000:0000:002a")
    assert(addrrange._format_ip6(0x1337 << 16) ==
        "0000:0000:0000:0000:0000:0000:1337:0000")
    assert(addrrange._format_ip6(24197857203266734884469844682461802258) ==
        "1234:5678:9abc:def1:2345:6789:abcd:ef12")


def test_parse_ip6():
    assert(addrrange._parse_ip6("0000:0000:0000:0000:0000:0000:0000:002a")
        == 42)
    assert(addrrange._parse_ip6("0000:0000:0000:0000:0000:0000:1337:0000")
        == 0x13370000)
    assert(addrrange._parse_ip6("1234:5678:9abc:def1:2345:6789:abcd:ef12")
        == 24197857203266734884469844682461802258)
    assert_raises(InvalidAddressError, addrrange._parse_ip6, "invalid")
    assert_raises(InvalidAddressError, addrrange._parse_ip6,
        "0000:0000:0000:00g0:0000:0000:0000:0000")
    # short form
    assert addrrange._parse_ip6("::") == 0
    assert addrrange._parse_ip6("::2a") == 42
    assert addrrange._parse_ip6("2a::") == 42 << 112
    assert(addrrange._parse_ip6("2a::1234:abcd") ==
        (42 << 112) + (0x1234 << 16) + 0xabcd)
    assert(addrrange._parse_ip6("2a:1234::5678:abcd") ==
        (42 << 112) + (0x1234 << 96) + (0x5678 << 16) + 0xabcd)


def test_ip6range():
    ipr = addrrange.Ip6Range("fc42:0f00:0ba2:cafe:1234:1234:1234:1234/64")
    assert(addrrange._format_ip6(ipr.net) ==
        "fc42:0f00:0ba2:cafe:0000:0000:0000:0000")
    assert ipr.mask == 64
    ipr = addrrange.Ip6Range("fc42:0f00:0ba2:cafe:1234:1234:efcd:1234/110")
    assert(addrrange._format_ip6(ipr.net) ==
        "fc42:0f00:0ba2:cafe:1234:1234:efcc:0000")
    assert ipr.mask == 110
    assert len(ipr) == 262144
    assert_raises(InvalidAddressError, addrrange.Ip6Range, "1.2.3.4")
    assert_raises(InvalidAddressError, addrrange.Ip6Range, "::1/154")
    assert_raises(InvalidAddressError, addrrange.Ip6Range, "42")

    assert ipr[262143] == "fc42:0f00:0ba2:cafe:1234:1234:efcf:ffff"
    assert_raises(IndexError, ipr.__getitem__, 262144)


def test_ip6range_contains():
    ipr = addrrange.Ip6Range("fc42:0f00:0ba2:cafe:1234:1234:efcd:1234/110")
    assert "fc42:0f00:0ba2:cafe:1234:1234:efcb:ffff" not in ipr
    assert "fc42:0f00:0ba2:cafe:1234:1234:efcc:0000" in ipr
    assert "fc42:0f00:0ba2:cafe:1234:1234:efce:1234" in ipr
    assert "fc42:0f00:0ba2:cafe:1234:1234:efcf:ffff" in ipr
    assert "fc42:0f00:0ba2:cafe:1234:1234:efd0:0000" not in ipr


def test_ip6range_str():
    ipr = addrrange.Ip6Range("fc42:0f00:0ba2:cafe:1234:1234:efcd:1234/110")
    assert str(ipr) == "fc42:0f00:0ba2:cafe:1234:1234:efcc:0000/110"
    ipr = addrrange.Ip6Range("feaf:1234:0000:0000:0000:0000:0000:1234/10")
    assert str(ipr) == "fe80:0000:0000:0000:0000:0000:0000:0000/10"


def test_addrset():
    addrs = addrrange.AddrSet()
    addrs.add("1.2.3.4")
    addrs.add("127.0.0.1")
    assert "127.0.0.1" in addrs and "1.2.3.4" in addrs
    addr = addrs.addr_set.pop()
    assert addr == "127.0.0.1" or addr == "1.2.3.4"
    addrs.add("iamanaddress")
    assert addrs.len() == 2
    addrs.remove("iamanaddress")
    assert addrs.len() == 1
    assert_raises(IndexError, addrs.__getitem__, 2)
