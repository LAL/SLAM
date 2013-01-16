"""This module contains all classes related to configuration file
generation.
"""

import sys, os, re, datetime, shutil
from django.db import models


class DuplicateRecordError(Exception):
    """Raised when a record already exists in a configuration file."""
    pass


class Config(models.Model):
    """Default behaviors for generator classes."""

    CONFIG_TYPE = (
        ("bind", "Bind generator"),
        ("rbind", "Reverse look-up Bind generator"),
        ("dhcp", "ISC-DHCPd generator"),
        ("quatt", "Quattor generator"),
        ("laldns", "LAL DNS generator")
    )

    comment = "#"
    conftype = models.CharField(max_length=6, choices=CONFIG_TYPE)
    default = models.BooleanField()
    outputfile = models.TextField()
    headerfile = models.TextField(blank=True, null=True)
    footerfile = models.TextField(blank=True, null=True)
    checkfile = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=50)
    timeout = models.CharField(max_length=10, blank=True, null=True)
    domain = models.TextField(blank=True, null=True)

    @classmethod
    def create(cls, childcls=None, name="", default=False, domain="",
            outputfile=None, header=None, footer=None, checkfile=None,
            update=False):
        """Initialize the input and output streams."""

        # This condition and the *childcls* have been added because I could not
        # find a way to properly call this method from an overidden inherited
        # class such as BindConfig.create.
        if cls.__name__ == "Config": # called from an overriden *create*
            config = childcls(name=name, default=default,
            conftype=childcls.type_, outputfile=outputfile, headerfile=header,
            footerfile=footer, checkfile=checkfile, domain=domain)
        else: # called directly
            config = cls(name=name, default=default, conftype=cls.type_,
                outputfile=outputfile, headerfile=header, footerfile=footer,
                checkfile=checkfile, domain=domain)

        config.output = None
        config.header = None
        config.footer = None

        if checkfile:
            config.checkfile = ", ".join(checkfile)

        return config

    def load(self):
        """Restore Config object after database get."""
        self.header = None
        self.footer = None
        self.check = None
        if not self.outputfile:
            self.output = None
        elif self.outputfile == "-":
            self.output = sys.stdout
        elif os.access(self.outputfile, os.R_OK | os.W_OK):
            self.output = open(self.outputfile, "r+")
        else:
            self.output = open(self.outputfile, "w")

        if self.headerfile:
            self.header = open(self.headerfile, "r")
        if self.footerfile:
            self.footer = open(self.footerfile, "r")

    def gen_header(self, header):
        """Copy the header to the output stream."""
        if not "output" in dir(self) or not self.output:
            self.load()

        for line in header:
            self.output.write(line)

    def gen_footer(self, footer):
        """Copy the footer to the output stream."""
        if not "output" in dir(self) or not self.output:
            self.load()

        for line in footer:
            self.output.write(line)

    def generate(self, hosts):
        """Generate the actual content of the file."""
        pass

    def _strip_slam_section(self, content):
        """Return the *content* with the slam section blanked to avoid
        false-positive in checkfile."""
        slambegin = (self.comment + " This section will be automatically "
            + "generated by SLAM any manual change will\n"
            + self.comment + " be overwritten on the next generation of this "
            + "file.\n")
        slamend = (self.comment + " END of section automatically generated by "
            + "SLAM\n")

        if slambegin not in content or slamend not in content:
            return content

        res = content[:content.find(slambegin)]
        res += "\n" * content[content.find(slambegin)
            :content.find(slamend) + len(slamend)].count("\n")
        res += content[content.find(slamend) + len(slamend):]

        return res

    def is_unique(self, hosts):
        """Check if all the hosts from *hosts* are not yet declared in the
        configurations files specified in *self.checkfile*. A list of duplicate
        records is returned."""
        if not "output" in dir(self) or not self.output:
            self.load()

        if not self.checkfile:
            return True

        res = []
        if not self.check:
            self.check = []
            for filename in self.checkfile.split(", "):
                file_ = open(filename, "r")
                content = self._strip_slam_section(file_.read())
                linenum = 1
                for line in content.split("\n"):
                    if self.comment in line:
                        line = line[:line.find(self.comment)]
                    if line:
                        for host, addr, _, _ in hosts:
                            if not host.name:
                                continue
                            if not self._unique_host(line, host, addr):
                                res.append((host, file_.name, linenum))
                    linenum += 1
                file_.close()

        return res

    def _unique_host(self, line, host, addrs):
        """Check that a given host does not already exists in the given
        line."""
        # implemented in child classes
        pass

    def backup(self):
        """Backup the existing configuration file to filename.timestamp."""
        if (self.outputfile and self.outputfile != "-"
                and os.access(self.outputfile, os.R_OK)
                and os.stat(self.outputfile).st_size > 0):
            shutil.copyfile(self.outputfile, self.outputfile + "-"
                + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))

    def createconf(self, genpools):
        """Create a new configuration file from the header, the content and the
        footer. It returns records found in the checkfile list."""
        if not "output" in dir(self) or not self.output:
            self.load()

        # search duplicates and remove them from *hosts*
        duplicates = []
        for _, hosts in genpools:
            tmp_dup = []
            if self.checkfile:
                tmp_dup = self.is_unique(hosts)
            hosts_tmp = [hostaddr[0] for hostaddr in hosts]
            for dup_host, _, _ in duplicates:
                if dup_host in hosts_tmp:
                    del hosts[hosts_tmp.index(dup_host)]
                    hosts_tmp.remove(dup_host)
            duplicates.extend(tmp_dup)

        self.output.seek(0)
        self.output.truncate()
        if self.header is not None:
            self.gen_header(list(self.header))
        self.output.write("\n" + self.comment + " This section will be "
            + "automatically generated by SLAM any manual change will\n"
            + self.comment
            + " be overwritten on the next generation of this file.\n")
        for pool, pool_hosts in genpools:
            if pool:
                self.output.write(self.comment + " Pool " + str(pool) + "\n")
            self.generate(pool_hosts)
        self.output.write(self.comment
            + " END of section automatically generated by SLAM\n")
        if self.footer is not None:
            self.gen_footer(list(self.footer))

        self.output.flush()
        return duplicates

    def updateconf(self, genpools):
        """Update an already existing configuration file and replace a
        previously existing content by a new regenerated one. It returns a list
        of duplicates records found in checkfile."""
        if not "output" in dir(self) or not self.output:
            self.load()

        # search duplicates and remove them from *hosts*
        duplicates = []
        for _, hosts in genpools:
            tmp_dup = []
            if self.checkfile:
                tmp_dup = self.is_unique(hosts)
            hosts_tmp = [hostaddr[0] for hostaddr in hosts]
            for dup_host, _, _ in tmp_dup:
                if dup_host in hosts_tmp:
                    del hosts[hosts_tmp.index(dup_host)]
                    hosts_tmp.remove(dup_host)
            duplicates.extend(tmp_dup)

        headers = []
        for line in self.output:
            headers.append(line)
            if (len(headers) > 1
                    and line == self.comment + " be overwritten on the next "
                        + "generation of this file.\n"
                    and headers[-2] == self.comment
                        + " This section will be automatically generated by "
                        + "SLAM any manual change will\n"):
                break

        footers = []
        for line in self.output:
            if (footers or line == self.comment
                    + " END of section automatically generated by SLAM\n"):
                footers.append(line)

        self.output.seek(0)
        self.output.truncate()
        if headers:
            self.gen_header(headers)
        for pool, hosts in genpools:
            if pool:
                self.output.write(self.comment + " Pool " + str(pool) + "\n")
            self.generate(hosts)
        if footers:
            self.gen_footer(footers)

        self.output.flush()
        return duplicates

    def __unicode__(self):
        res = (self.name + " (" + self.conftype + "), output file: \""
            + self.outputfile + "\"")
        if self.default:
            res += ", default"
        return res


def _update_soa(soa):
    """Increment a SOA record, respecting RFC1912."""
    soa = soa.strip()
    idx = soa.find("SOA") + 3

    values = soa[idx:].split()
    if not re.match("[0-9]{10}", values[2]):
        raise ValueError("Cannot parse SOA record: unrecognized format")

    date = values[2][:-2]
    serial = int(values[2][-2:])
    today = datetime.date.today().strftime("%Y%m%d")
    if date == today:
        if serial == 99:
            raise ValueError("SOA serial overflow: current value is 99")
        serial = serial + 1
    else:
        date = today
        serial = 1
    values[2] = date + "{0:02}".format(serial)

    return soa[:idx] + " " + " ".join(values) + "\n"


class BindConfig(Config):
    """Represents the configuration of the DNS server Bind that can generate
    parametered configuration lines for hosts."""

    comment = ";"
    type_ = "bind"

    class Meta:
        """BindConfig is a proxy of Config."""
        proxy = True

    @classmethod
    def create(cls, name="", default=False, domain="", outputfile=None,
            header=None, footer=None, checkfile=None, update=False,
            timeout="1D"):
        """Initialize the Bind config generator with the given *timeout* for
        name records."""
        if timeout is None:
            timeout = "1D"

        config = Config.create(childcls=BindConfig, name=name,
            outputfile=outputfile, header=header, footer=footer,
            checkfile=checkfile, update=update)
        config.timeout = timeout
        return config

    def _unique_host(self, line, host, addr):
        """Check if the record for a host already exists in the checkfiles."""
        records = line.split()
        name = records[0]
        return not (host.name == name
            or ("." in name and host.name == name[:name.find(".")])
            or (addr and addr.addr and addr.addr == records[-1]))

    def gen_header(self, header):
        """Copy the orignial header and update the SOA field."""
        for line in header:
            if "SOA" in line:
                line = _update_soa(line)
            self.output.write(line)

    def generate(self, hosts):
        """Generate one configuration record per address for every host given
        in the Bind format line."""
        for host, addr, _, _ in hosts:
            if host.nodns:
                continue
            self.output.write(host.name + "\t" + str(self.timeout)
                + "\tIN\t" + addr.pool.dns_record + "\t"
                + str(addr) + "\n")


class RevBindConfig(Config):
    """Represent a generator for reverse DNS zone for the bind zone format."""

    comment = ";"
    type_ = "rbind"

    class Meta:
        """RevBindConfig is a proxy of Config."""
        proxy = True

    def _unique_host(self, line, host, addr):
        """Check if the record for a host already exists in the checkfiles."""
        records = line.split()
        name = records[-1]
        return not (host.name == name
            or ("." in name and host.name == name[:name.find(".")])
            or (addr and addr.addr and addr.addr == records[0]))

    @classmethod
    def create(cls, name="", default=False, domain="", outputfile=None,
            header=None, footer=None, checkfile=None, update=False,
            timeout="1D"):
        """Initialize the RevBind config generator with the given *timeout* for
        name records."""
        if timeout is None:
            timeout = "1D"

        config = Config.create(childcls=RevBindConfig, name=name,
            outputfile=outputfile, header=header, footer=footer,
            checkfile=checkfile, update=update)
        config.timeout = timeout
        return config

    def generate(self, hosts):
        """Generate a reverse mapping for Addresses"""
        for host, addr, _, _ in hosts:
            if host.nodns:
                continue
            if addr.pool.addr_range_type == "ip4":
                split = str(addr).split(".")
                rev = "in-addr.arpa."
                for atom in split:
                    rev = atom + "." + rev
            elif addr.pool.addr_range_type == "ip6":
                addr = str(addr).replace(":", "")
                rev = "ip6.arpa."
                for digit in addr:
                    rev = digit + "." + rev
            else:
                continue
            self.output.write(rev + "\t" + str(self.timeout)
                + "\tIN\tPTR\t" + host.name + "\n")


class QuattorConfig(Config):
    """Class used to generate the Quattor configuration file for a host."""

    type_ = "quatt"

    class Meta:
        """QuattorConfig is a proxy of Config."""
        proxy = True

    def _unique_host(self, line, host, addr):
        """Check if the record for a host already exists in the checkfiles."""
        name = line.split("\"")[1]

        return not (host.name == name
            or ("." in name[1] and host.name == name[:name.find(".")])
            or (addr and addr.addr and addr.addr in line))

    def generate(self, hosts):
        """Generate a configuration for every hosts for a Quattor configuration
        file."""
        for host, addr, _, _ in hosts:
            self.output.write('escape("' + host.name + '"),"'
                + str(addr) + '",\n')


class DhcpdConfig(Config):
    """Generate a host line usable by isc-DHCPd."""

    type_ = "dhcp"

    class Meta:
        """QuattorConfig is a proxy of Config."""
        proxy = True

    def _unique_host(self, line, host, addr):
        """Check if the record for a host already exists in the checkfiles."""
        records = line.split()
        if (addr and addr.macaddr and (addr.macaddr in records
                or addr.macaddr + ";" in records)):
            return False

        if "host" not in line or len(line.split()) <= 1:
            return True

        name = line[line.find("host"):].split()[1]
        return "host" not in line or not (host.name == name
            or ("." in name and host.name == name[:name.find(".")]))

    def generate(self, hosts):
        """Generate a configuration file of the static address configuration
        of hosts for isc-DHCP."""

        if self.domain:
            self.output.write("option domain-name \"" + self.domain + "\";\n")

        for host, addr, _, _ in hosts:
            if addr.macaddr:
                line = "host " + host.name + " { "
                line += "hardware ethernet " + addr.macaddr + "; "
                line += "fixed-address " + str(host.name) + "; }\n"
                self.output.write(line)


class LalDnsConfig(Config):
    """Generator for the configuration format of the LAL custom DNS format."""

    type_ = "laldns"

    class Meta:
        """LalDns is a proxy of Config."""
        proxy = True

    def _unique_host(self, line, host, addr):
        """Check that the current record does not already exist in
        checkfiles."""
        records = line.split()
        return not (host.name in records[1:]
            or (addr and addr.addr and addr.addr in records))

    def generate(self, hosts):
        """Generate configuration for the specific format of DNS configuration
        file used by the LAL."""
        for host, addr, aliases, mx_record in hosts:
            if host.nodns:
                continue
            alias = ""
            for aliasobj in aliases:
                alias += "\t" + aliasobj.name
            self.output.write(str(addr) + "\t" + host.name
                + alias + "\t" + mx_record + "\n")
