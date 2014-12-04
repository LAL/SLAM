"""Contains classes that represent a collection of addresses."""

import re

class InvalidAddressError(Exception):
    """The format of the given address was not recognized."""
    pass


def _format_ip4(addr):
    """Return a string holding the human-friendly version of the IPv4
    address *addr* in an integer representation.
    """
    res = ""
    res = res + str(addr >> 24) + "."
    res = res + str((addr >> 16) & 0xff) + "."
    res = res + str((addr >> 8) & 0xff) + "."
    res = res + str(addr & 0xff)
    return res


def _parse_ip4(addr):
    """Return the integer representation of the given address *addr* in a
    human-friendly format (255.255.255.255).
    """
    match = re.match(r"([0-9]{1,3})\." * 3 + r"([0-9]{1,3})", addr)
    if match is None:
        raise InvalidAddressError("Invalid IPv4 address: " + addr)
    res = 0
    for i in range(1, 5):
        try:
            if int(match.group(i)) > 255:
                raise ValueError("Invalid IPv4 address: " + addr)
            res = res * 256 + int(match.group(i))
        except ValueError:
            raise InvalidAddressError("Invalid IPv4 address: " + addr)
    return res


class Ip4Range:
    """Represents an IPv4 subnet."""

    range_type = 'ip4'
    dns_record = 'A'

    def sortable(self, addr):
        """Returns a sortable representation of an address from this range."""
        return _parse_ip4(addr.addr)

    def __init__(self, iprange):
        """Initialize the range with the given subnet *iprange* with format
        x.x.x.x/x."""
        subnet_pos = iprange.find("/")
        if subnet_pos < 0 or iprange.count(".") != 3:
            raise InvalidAddressError("Invalid IPv4 range definition: "
                + iprange)
        self.net = _parse_ip4(iprange[:subnet_pos])
        self.mask = int(iprange[subnet_pos + 1:])
        if self.net < 0 or self.net > 2**32 or self.mask < 0 or self.mask > 32:
            raise InvalidAddressError("Invalid IPv4 range definition: "
                + iprange)
        #get the real subnet address: clear the 32 - mask last bits
        self.net = self.net & ((2 ** (self.mask + 1) - 1) << (32 - self.mask))

    def __iter__(self):
        """Iterator over the IPv4 subnet."""
        for i in xrange(self.net, self.net + 2 ** (32 - self.mask)):
            yield _format_ip4(i)

    def __contains__(self, addr):
        """Return true if the given *addr* belongs to this subnet."""
        try:
            addr = _parse_ip4(addr)
        except InvalidAddressError:
            return False
        return addr >= self.net and addr < self.net + 2 ** (32 - self.mask)

    def len(self):
        """Return the number of addresses in this subnet."""
        return 2 ** (32 - self.mask)

    def __len__(self):
        """Return the number of addresses in this subnet."""
        return self.len()

    def __getitem__(self, ind):
        """Return the formatted addresses at index *n* from the subnet."""
        # Allow the use of random.choice(Ip4Range)
        if ind < 0 or ind >= 2 ** (32 - self.mask):
            raise IndexError()
        return _format_ip4(self.net + ind)

    def __str__(self):
        """Return a human-readable representation of the subnet."""
        return _format_ip4(self.net) + "/" + str(self.mask)


def _format_ip6(addr):
    """Return a string holding the human-friendly version of the IPv6
    address *addr* in an integer representation.
    """
    power = 112
    res = ""
    while power > 0:
        # in format strings the arguments must be numbered before python2.7
        res = res + "{0:04x}".format((addr >> power) & 0xffff) + ":"
        power = power - 16
    res = res + "{0:04x}".format(addr & 0xffff)
    return res


def _parse_ip6(addr):
    """Return the integer representation of the given address *addr* in a
    human-friendly format (19af:1234::abcd).
    """
    if addr == "::":
        addr = (":0" * 8)[1:] # strip the initial ':'
    elif addr.find("::") >= 0:
        abbrev = addr.find("::")
        groups = addr.count(":")
        if abbrev == 0 or abbrev == len(addr) - 2:
            groups = groups - 1
        add = (":0" * (8 - groups))[1:] # strip the initial ':'
        if abbrev == 0: # expend the beginning
            addr = add + addr[abbrev + 1:]
        elif abbrev == len(addr) - 2: #expend the end
            addr = addr[:abbrev + 1] + add
        else:
            addr = addr[:abbrev + 1] + add + addr[abbrev + 1:]

    match = re.match("([a-fA-F0-9]{1,4}):" * 7 + "([a-fA-F0-9]{1,4})", addr)
    if match is None:
        raise InvalidAddressError("Invalid IPv6 address: " + addr)
    res = 0
    for i in range(1, 9):
        try:
            res = res * (2 ** 16) + int(match.group(i), 16)
        except ValueError:
            raise InvalidAddressError("Invalid IPv6 address: " + addr)
    return res


class Ip6Range:
    """Represents an IPv6 subnet."""

    range_type = "ip6"
    dns_record = "AAAA"

    def sortable(self, addr):
        """Returns a sortable representation of an address from this range."""
        return _parse_ip6(addr.addr)

    def __init__(self, iprange):
        """Initialize the range with the given subnet *iprange* with format
        12ab:34cd::89ef/x.
        """
        subnet_pos = iprange.find("/")
        if subnet_pos < 0:
            raise InvalidAddressError("Invalid IPv6 range: " + iprange)
        self.net = _parse_ip6(iprange[:subnet_pos])
        self.mask = int(iprange[subnet_pos + 1:])
        if (self.net < 0 or self.net > 2**128 or
                self.mask < 0 or self.mask > 128):
            raise InvalidAddressError("Invalid IPv6 range: " + iprange)
        #get the real subnet address: clear the (128 - mask) last bits
        self.net = self.net & ((2 ** (self.mask + 1) - 1) << (128 - self.mask))

    def __iter__(self):
        """Iterator over the IPv6 subnet."""
        # IPv6 addresses are too big for xrange()
        i = self.net
        while i < self.net + 2 ** (128 - self.mask):
            yield _format_ip6(i)
            i = i + 1

    def __contains__(self, addr):
        """Return true if the given *addr* belongs to this subnet."""
        try:
            addr = _parse_ip6(addr)
        except InvalidAddressError:
            return False
        return addr >= self.net and addr < self.net + 2 ** (128 - self.mask)

    def len(self):
        """Return the number of addresses in this subnet."""
        return 2 ** (128 - self.mask)

    def __len__(self):
        """Return the number of addresses in this subnet."""
        return self.len()

    def __getitem__(self, ind):
        """Return the formatted addresses at index *n* from the subnet."""
        # Allow the use of random.choice(Ip6Range)
        if ind < 0 or ind >= 2 ** (128 - self.mask):
            raise IndexError()
        return _format_ip6(self.net + ind)

    def __str__(self):
        """Return a human-readable representation of the subnet."""
        return _format_ip6(self.net) + "/" + str(self.mask)


class AddrSet:
    """Represent a generic set of addresses. The addresses must be added
    manually.
    """

    range_type = "set"

    def sortable(self, addr):
        """Returns a sortable representation of an address from this range."""
        return addr.addr

    def __init__(self, addr_set=None, dns_record="A"):
        """Initialize a new address set of DNS record type *dns_record*."""
        self.addr_set = addr_set
        if self.addr_set is None:
            self.addr_set = set()
        self.dns_record = dns_record

    def add(self, addr):
        """Add the address *addr* to the set."""
        self.addr_set.add(addr)

    def remove(self, addr):
        """Remove the address *addr* from the set."""
        self.addr_set.remove(addr)

    def __contains__(self, addr):
        return addr in self.addr_set

    def __iter__(self):
        return iter(self.addr_set)

    def len(self):
        """Return the number of elements in the set."""
        return len(self.addr_set)

    def __len__(self):
        return self.len()

    def __getitem__(self, ind):
        if ind < 0 or ind >= len(self):
            raise IndexError()
        for addr in self:
            if (ind == 0):
                return addr
            ind = ind - 1

    def __str__(self):
        res = ""
        for elm in self.addr_set:
            res = res + "," + str(elm)
        # skip the first comma
        return res[1:]
