"""Module containing all the models used by the SLAM application."""

import random
from django.db import models

from slam import addrrange

class FullPoolError(Exception):
    """The pool does not have any available addresses."""
    pass


class AddressNotInPoolError(Exception):
    """The given address does not belong to this pool."""
    pass


class AddressNotAllocatedError(Exception):
    """The given address was not allocated."""
    pass


class AddressNotAvailableError(Exception):
    """The given address is already allocated."""
    pass

from slam.generator import Config
from slam.log import LogEntry

class Host(models.Model):
    """Represent a computer or device connectable to the network and that can
    have one or several network addresses.
    """

    name = models.CharField(max_length=50)
    category = models.CharField(max_length=20, blank=True)
    serial = models.CharField(max_length=50, blank=True)
    inventory = models.CharField(max_length=50, blank=True)

    def __unicode__(self):
        return self.name


class Alias(models.Model):
    """An alias name for another host. The type is used to differentiate
    whether the alias points to the host's name or the host's address."""

    ALIAS_TYPE = (
        ("name", "Name"),
        ("addr", "Address"),
    )

    aliastype = models.CharField(choices=ALIAS_TYPE, max_length=4,
        default="name")
    name = models.CharField(max_length=50)
    host = models.ForeignKey(Host)

    def __unicode__(self):
        return self.name


class Pool(models.Model):
    """Define a pool of addresses, keeping track of which addresses are in
    use."""

    ADDR_RANGE_CHOICE = (
        ('ip4', 'IPv4 subnet'),
        ('ip6', 'IPv6 subnet'),
        ('set', 'Address set'),
    )

    name = models.CharField(max_length=50, blank=True)
    category = models.TextField(blank=True)
    addr_range_type = models.CharField(max_length=5, choices=ADDR_RANGE_CHOICE)
    addr_range_str = models.TextField(blank=True)
    dns_record = models.CharField(max_length=10)
    addr_range = None
    generator = models.ManyToManyField(Config)

    @classmethod
    def create(cls, name=None, addr_range=None,
            definition=None, category=""):
        """Initialize a Pool object of name *name* and unallocated address
        space *addr_range*.
        """
        if definition is not None:
            if definition.find(".") >= 0:
                addr_range = addrrange.Ip4Range(definition)
            elif definition.find(":") >= 0:
                addr_range = addrrange.Ip6Range(definition)
            elif definition.find(",") >= 0:
                addr_range = addrrange.AddrSet(set(definition.split(",")))
            else:
                addr_range = addrrange.AddrSet()

        pool = cls(name=name, addr_range_type=addr_range.range_type,
            addr_range_str=str(addr_range), dns_record=addr_range.dns_record,
            category=category)
        pool.addr_range = addr_range
        return pool

    def _update(self):
        """Restore an address range class from the serialized data."""
        if self.addr_range_type == 'ip4':
            self.addr_range = addrrange.Ip4Range(self.addr_range_str)
        elif self.addr_range_type == 'ip6':
            self.addr_range = addrrange.Ip6Range(self.addr_range_str)
        else: # set
            addrset = set()
            if len(self.addr_range_str) > 0:
                addrset = set(str(self.addr_range_str).split(","))
            self.addr_range = addrrange.AddrSet(addrset, self.dns_record)

    def get(self):
        """Get the first available address in the pool."""
        if self.addr_range is None:
            self._update()
        res = None
        for addr in self.addr_range:
            if res is not None:
                break
            if not Address.objects.filter(
                    allocated=True, pool=self, addr=addr):
                res = addr
        if res is None:
            raise FullPoolError("The pool \"" + self.name + "\" is full.")
        addr = Address(addr=res, allocated=True, pool=self)
        addr.save()
        return addr

    def get_rand(self):
        """Get a random available address in the pool."""
        if self.addr_range is None:
            self._update()
        len_ = self.addr_range.len()
        i = len_
        res = None
        while i > 0 and res is None:
            i = i - 1
            addr = self.addr_range[random.randint(0, len_ - 1)]
            if not Address.objects.filter(
                    allocated=True, pool=self, addr=addr):
                res = addr

        # no result with the random: either the pull is full or we were unlucky
        if res is None:
            # try the linear method
            return self.get()
        else:
            addrobj = Address(addr=res, allocated=True, pool=self)
            addrobj.save()

        return addrobj

    def allocate(self, addr, host=None):
        """Mark the address *addr* of the pool as allocated."""
        if self.addr_range is None:
            self._update()
        if addr not in self.addr_range:
            raise AddressNotInPoolError("Address \"" + addr
                + "\" is not in pool: " + self.name)
        if Address.objects.filter(allocated=True, pool=self, addr=addr):
            raise AddressNotAvailableError("Address \"" + addr
                + "\" is not available.")
        if host is None:
            newaddr = Address(addr=addr, allocated=True, pool=self)
        else:
            newaddr = Address(addr=addr, allocated=True, pool=self, host=host)
        newaddr.save()
        return newaddr

    def free(self, addr):
        """Mark the address *addr* of the pool as available."""
        if self.addr_range is None:
            self._update()
        if addr not in self.addr_range:
            raise AddressNotInPoolError("Could not delete address \"" + addr
                + "\": the address is not in the given pool")

        addr_qs = Address.objects.filter(addr=addr, allocated=True, pool=self)
        if addr_qs.count() == 0:
            raise AddressNotAllocatedError("Could not delete address \"" + addr
                + "\": the address is not allocated")
        addr_qs.delete()

    def isallocated(self, addr):
        """Return true if the address *addr* is already in use."""
        if self.addr_range is None:
            self._update()
        if addr not in self.addr_range:
            raise AddressNotInPoolError("Address \"" + addr
                + "\" is not in the pool: " + self.name)
        return Address.objects.filter(allocated=True, pool=self, addr=addr)

    def __contains__(self, addr):
        if self.addr_range is None:
            self._update()
        return (Address.objects.filter(allocated=True, pool=self, addr=addr)
            or addr in self.addr_range)

    def len(self):
        """Return the number of element in the range."""
        if self.addr_range is None:
            self._update()
        return self.addr_range.len()

    def __unicode__(self):
        if self.addr_range is None:
            self._update()
        return self.name + " (range: " + str(self.addr_range) + ")"


class Address(models.Model):
    """Represent a network address."""

    addr = models.CharField(max_length=40, blank=True)
    macaddr = models.CharField(max_length=17, blank=True)
    allocated = models.BooleanField(default=False)
    pool = models.ForeignKey(Pool, blank=True, null=True)
    host = models.ForeignKey(Host, null=True, blank=True)
    date = models.DateTimeField(auto_now=True)
    duration = models.DateTimeField(blank=True, null=True, default=None)
    lastuse = models.DateTimeField(blank=True, null=True)

    def __unicode__(self):
        return self.addr


class Property(models.Model):
    """Represent a property of an object."""

    name = models.CharField(max_length=20)
    value = models.TextField()
    pool = models.ForeignKey(Pool, blank=True, null=True)
    host = models.ForeignKey(Host, blank=True, null=True)

    def __unicode__(self):
        return self.name + ": " + self.value
