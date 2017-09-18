"""Helper to execute actions on the database independantly from the interface
and output format."""

import logging, datetime, sys, re
from slam import generator, models
from slam.log import DbLogHandler


# set-up logging to the database
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
DBLOGHANDLER = DbLogHandler()
DBLOGHANDLER.setLevel(logging.INFO)
LOGGER.addHandler(DBLOGHANDLER)
STDOUTHANDLER = logging.StreamHandler()
STDOUTHANDLER.setLevel(logging.INFO)
LOGGER.addHandler(STDOUTHANDLER)


class InexistantObjectError(Exception):
    """Exception raised when the given object name was not found in the
    database."""
    pass


class DuplicateObjectError(Exception):
    """Exception raised when trying to create an object that already exists."""
    #def _get_message(self): 
    #    return self._message
    #def _set_message(self, message): 
    #    self._message = message
    #message = property(_get_message, _set_message)
    #def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        #Exception.__init__(self, message)
    pass


class MissingParameterError(Exception):
    """Exception raised when a parameter is missing."""
    pass


class ConfigurationFormatError(Exception):
    """Exception raised when the given configuration format is not
    supported."""
    pass


class PropertyFormatError(Exception):
    """Exception raised if the property format is invalid."""
    pass

def isValidHostname(hostname):
    disallowed = re.compile("[^a-zA-Z\d\-]")
    #return all(map(lambda x: len(x) and not disallowed.search(x), hostname.split("."))) //pour chaque x dans split array(),appliquer les functions len(x) and not disallowed.search(x)
    return len(hostname) and not disallowed.search(hostname)

def get_host(host_name=None):
    """Retrieve a host object from the database."""
    host = None

    if host_name:
        if models.Host.objects.filter(name=host_name):
            host = models.Host.objects.get(name=host_name)
        elif models.Alias.objects.filter(name=host_name):
            host = models.Alias.objects.get(name=host_name).host
        else:
            raise InexistantObjectError("Could not find host named: "
                + str(host_name))

    return host


def get_pool(pool_name=None, category=None):
    """Retrieve a pool object from the database."""
    if pool_name:
        if not models.Pool.objects.filter(name=pool_name).count():
            raise InexistantObjectError("Could not find pool named: "
                + str(pool_name))
        return models.Pool.objects.get(name=pool_name)
    elif category:
        for poolobj in models.Pool.objects.exclude(category=""):
            if category in poolobj.category.split(","):
                return poolobj
        raise InexistantObjectError("No pool in category: " + category)
    else:
        return None


def create_pool(pool_name=None, definition=None, category=None):
    """Try to retrieve the given *pool_name* from the database or a create a
    new one with the given *definition* otherwise."""
    if models.Pool.objects.filter(name=pool_name):
        raise DuplicateObjectError("Pool named \""
            + pool_name + "\" already exists.")
    if not pool_name:
        raise MissingParameterError("Missing a name for the pool to create.")
    if not definition:
        raise MissingParameterError("Missing pool definition.")
    if category is None:
        category = ""
    else:
        category = ",".join(category)
    pool = models.Pool.create(name=pool_name, definition=definition,
        category=category)
    LOGGER.info("Created pool: " + str(pool))
    pool.save()

    return pool


def create_generator(name, type_, outputfile, default=False, header=None,
        footer=None, checkfile=None, timeout=None, domain=None, pools=None):
    """Create a new generator object."""
    if name and models.Config.objects.filter(name=name):
        raise DuplicateObjectError("Generator \"" + name
            + "\" already exists.")
    if not name:
        raise MissingParameterError(
            "You must provide a name for the new generator.")
    if not type_:
        raise MissingParameterError(
            "You must provide a type for the new generator.")
    if not outputfile:
        raise MissingParameterError(
            "You must provide an output file for the new generator.")

    genobj = None
    if type_ == "bind":
        genobj = generator.BindConfig.create(name=name, default=default,
            outputfile=outputfile, header=header, footer=footer,
            checkfile=checkfile, update=True, timeout=timeout)
    elif type_ == "revbind":
        genobj = generator.RevBindConfig.create(name=name, default=default,
            outputfile=outputfile, header=header, footer=footer,
            checkfile=checkfile, update=True, timeout=timeout)
    elif type_ == "dhcp":
        genobj = generator.DhcpdConfig.create(name=name, default=default,
            outputfile=outputfile, header=header, footer=footer,
            checkfile=checkfile, update=True)
    elif type_ == "quattor":
        genobj = generator.QuattorConfig.create(name=name, default=default,
            outputfile=outputfile, header=header, checkfile=checkfile,
            footer=footer, update=True)
    elif type_ == "laldns":
        genobj = generator.LalDnsConfig.create(name=name, default=default,
            outputfile=outputfile, header=header, checkfile=checkfile,
            footer=footer, update=True)
    else:
        raise MissingParameterError("Wrong configuration format: " + type_)
    genobj.save()

    LOGGER.info("Created new generator: " + str(genobj))
    if pools:
        for pool in pools:
            pool = get_pool(pool)
            pool.generator.add(genobj)

    genobj.save()
    return genobj


def get_generator(name):
    """Get the correct configuration generator object."""
    genobj = None

    if name:
        if not models.Config.objects.filter(name=name):
            raise InexistantObjectError("Could not find generator: "
                + name)

        confobj = models.Config.objects.get(name=name)
        if confobj.conftype == "bind":
            genobj = generator.BindConfig.objects.get(name=name)
        elif confobj.conftype == "rbind":
            genobj = generator.RevBindConfig.objects.get(name=name)
        elif confobj.conftype == "dhcp":
            genobj = generator.DhcpdConfig.objects.get(name=name)
        elif confobj.conftype == "quatt":
            genobj = generator.QuattorConfig.objects.get(name=name)
        elif confobj.conftype == "laldns":
            genobj = generator.LalDnsConfig.objects.get(name=name)
        else:
            raise InexistantObjectError("Could not find generator: "
                + name)

    return genobj


def get_default_generators(conf_type=None):
    """Get every generators marked as default, eventually filtered by
    configuration type."""
    gens = generator.Config.objects.filter(default=True)
    if conf_type:
        gens = gens.filter(conftype=conf_type)

    res = []
    for gen in gens:
        tmp = get_generator(gen.name)
        if tmp:
            res.append(tmp)

    return res


def modify_generator(name, default=False, outputfile=None, header=None,
        footer=None, checkfile=None, timeout=None, domain=None, pools=None):
    """Modify an existing generator."""
    gen = get_generator(name)
    if gen is None:
        raise InexistantObjectError("Could not find generator: " + name)

    logmsg = ""
    if default:
        gen.default = not gen.default
        if gen.default:
            logmsg += ", set as default"
        else:
            logmsg += ", removed default"
    if outputfile:
        gen.outputfile = outputfile
        logmsg += ", new output file (" + str(outputfile) + ")"
    if header:
        gen.headerfile = header
        logmsg += ", new header file (" + str(header) + ")"
    if footer:
        gen.footerfile = footer
        logmsg += ", new footer file (" + str(footer) + ")"
    if checkfile:
        gen.checkfile = ", ".join(checkfile)
        logmsg += ", new check files (" + str(checkfile) + ")"
    if timeout:
        gen.timeout = timeout
        logmsg += ", new timeout (" + str(timeout) + ")"
    if domain:
        gen.domain = domain
        logmsg += ", new domain (" + str(domain) + ")"
    if pools:
        gen.pool_set.clear()
        for pool in pools:
            gen.pool_set.add(get_pool(pool))
            logmsg += ", new pool (" + str(pool.name) + ")"

    # skip the first comma
    if logmsg:
        logmsg = logmsg[1:]

    LOGGER.info("Modified generator " + str(name) + logmsg)
    gen.save()


def generate(gen_name=None, pool_name=None, conf_format=None,
        output=None, header=None, footer=None, checkfile=None, timeout=None,
        domain=None, update=True):
    """Generate a specified configuration file for the addresses in the given
    pool. It returns a list of duplicate records found in the checkfile of the
    generator."""
    pools = []
    if pool_name:
        for pool in pool_name:
            pools.append(get_pool(pool))

    gens = []
    gen = None
    if gen_name:
        gen = get_generator(gen_name)
    elif not conf_format and not output:
        gens = get_default_generators(conf_format)
    else:
        if conf_format == "bind":
            gen = generator.BindConfig.create(outputfile=output, header=header,
                footer=footer, checkfile=checkfile, timeout=timeout,
                update=update, domain=domain)
        elif conf_format == "revbind":
            gen = generator.RevBindConfig.create(outputfile=output,
                header=header, footer=footer, checkfile=checkfile,
                timeout=timeout, update=update, domain=domain)
        elif conf_format == "dhcp":
            gen = generator.DhcpdConfig.create(outputfile=output,
                header=header, footer=footer, checkfile=checkfile,
                update=update, domain=domain)
        elif conf_format == "quattor":
            gen = generator.QuattorConfig.create(outputfile=output,
                header=header, footer=footer, checkfile=checkfile,
                update=update, domain=domain)
        elif conf_format == "laldns":
            gen = generator.LalDnsConfig.create(outputfile=output,
                header=header, footer=footer, checkfile=checkfile,
                update=update, domain=domain)
        else:
            raise ConfigurationFormatError(
                "Unknown configuration format: " + str(conf_format))

    # Individual generators are treated as a list of one generator
    if (not gens) and gen:
        gens = [gen]

    duplicates = []
    for gen in gens:
        if "output" not in gen.__dict__ or not gen.output:
            gen.load()

        relatedpools = models.Pool.objects.filter(generator__name=gen.name,
                generator__conftype=gen.conftype)
        if relatedpools:
            pools = list(relatedpools)

        genpools = []
        if not pools:
            pools = models.Pool.objects.all()
        for pool in pools:
            hosts = []
            for addr in models.Address.objects.filter(pool=pool):
                if addr.host:
                    mx_record = ""
                    if models.Property.objects.filter(
                            name="mx", host=addr.host):
                        mx_record = models.Property.objects.get(
                            name="mx", host=addr.host).value
                    hosts.append((addr.host,
                        addr, addr.host.alias_set.all(), mx_record))
            genpools.append((pool, hosts))

        gen.backup()
        poolmsg = ""
        if pools:
            poolmsg = " for pool " + ", ".join([pool.name for pool in pools])
        if update:
            LOGGER.info("Update configuration with generator " + str(gen)
                + poolmsg)
            duplicates.extend(gen.updateconf(genpools))
        else:
            LOGGER.info("Create new configuration with generator " + str(gen)
                + poolmsg)
            duplicates.extend(gen.createconf(genpools))

    for dup_host, dup_file, dup_line in duplicates:
        LOGGER.warn("Duplicate record: a record already exists for "
            + "host " + str(dup_host) + " in file " + dup_file
            + " at line " + str(dup_line))

    return duplicates


def allocate_address(pool, host=None, address=None, random=False,
    category=None, duration=None):
    """Allocate a new address from *pool* to *host*."""
    if not pool:
        if address:
            for poolobj in models.Pool.objects.all():
                poolobj._update()
                if (poolobj.addr_range is not None
                        and address in poolobj.addr_range):
                    pool = poolobj
                    break
        elif category:
            print("foo")
            pool = get_pool(None, category)
        else:
            raise MissingParameterError("Could not find a pool for the given"
                " pool name, category or address.")

    addr = None
    if host:
        if address:
            addr = pool.allocate(address, host)
        else:
            pools = [pool]
            if category:
                for poolobj in models.Pool.objects.all():
                    if (poolobj != pool
                            and  category in pool.category.split(",")):
                        pools.append(pool)
            for poolobj in pools:
                try:
                    if random:
                        addr = poolobj.get_rand()
                    else:
                        addr = poolobj.get()
                    if addr:
                        break
                except models.FullPoolError:
                    pass

        if addr:
            LOGGER.info("Assign address " + str(addr) + " to host "
                + str(host))
            addr.host = host
            emptyaddrs = host.address_set.exclude(macaddr="").filter(addr="")
            if emptyaddrs:
                addr.macaddr = emptyaddrs[0].macaddr
                emptyaddrs[0].delete()
            addr.save()
        else:
            if category:
                msg = ("No address available in pools from category "
                    + category)
            else:
                msg = "No address available in pool " + pool.name
            LOGGER.error(msg)
            raise models.FullPoolError(msg)
    else:
        addr = pool.allocate(address)
        LOGGER.info("Reserve address " + str(addr) + " in pool " + pool.name)

    if duration:
        addr.duration = (datetime.datetime.now() +
            datetime.timedelta(days=duration))
        addr.save()

    return addr


def create_host(host, pool=None, address=None, mac=None, random=False,
    alias=None, category=None, serial="", inventory="", duration=None,
    nodns=False):
    """Create a new host and assign it the first element of addesses or
    automatically one from the given pool, eventually random."""
    #validation
    if not host:
        raise MissingParameterError(
            "You must provide a name for the new host.")
    if not isValidHostname(hostname=host):
        raise PropertyFormatError(
            "You must provide a valid name (without space, special character) for the new host.")
        
    if models.Host.objects.filter(name=host):
        raise DuplicateObjectError("Host as the host name [" + host + "] already exists.")
    #anomalie9
    if models.Alias.objects.filter(name=host):
        raise DuplicateObjectError("A alias as the host name [" + host + "] already exists.")
    if alias:
        for alia in alias:
            if not isValidHostname(hostname=alia):
                raise PropertyFormatError("You must provide a valid alias name (without space, special character) for the new host.")
            if models.Alias.objects.filter(name=alia):
                raise DuplicateObjectError("A alias as alias name [" + str(alia) + "] already exists.")
            if models.Host.objects.filter(name=alia):
                raise DuplicateObjectError("A Host as alias name [" + str(alia) + "] already exists.")
            if host==alia:
                raise DuplicateObjectError("Host should not be equel to a alias name [" + str(alia) + "].")
    #fin anomalie9
    hostobj = models.Host(name=host)
    
    if not alias:
        alias = []
    
    logmac = ""
    if mac:
        logmac = " (mac: " + str(mac) + ")"
    LOGGER.info("Create new host \"" + str(host) + logmac + "\".")

    if category:
        hostobj.category = category
    if serial:
        hostobj.serial = serial
    if inventory:
        hostobj.inventory = inventory
    if nodns:
        hostobj.nodns = True
    hostobj.save()

    for alia in alias:
        if models.Alias.objects.filter(name=alia):
            LOGGER.warn("Alias " + str(alia) + " already exists and refers to "
                + models.Alias.objects.get(name=alia).host.name)
        else:
            aliasobj = models.Alias(name=alia, host=hostobj)
            aliasobj.save()

    if pool or category or address:
        addrobj = allocate_address(pool, hostobj, address, random, category)
        pool = addrobj.pool
        addrres = str(addrobj)
        if duration:
            addrobj.duration = (
                addrobj.date + datetime.timedelta(days=duration))
            addrobj.save()

        if mac:
            if addrobj:
                addrobj.macaddr = mac
                addrobj.save()
            elif hostobj.address_set.all():
                first_addr =  hostobj.address_set.all()[0]
                first_addr.macaddr = mac
                first_addr.save()
        LOGGER.info("Assigned address " + addrres + " to " + str(host)
            + " from pool " + pool.name)
        return str(hostobj), addrres
    else:
        if mac:
            addrobj = models.Address(macaddr=mac, host=hostobj)
            addrobj.save()
        return str(hostobj), None


def delete(pool=None, addresses=None, hosts=None):
    """Delete objects from the database: address, host or pool."""
    if addresses:
        for addr in addresses:
            if not models.Address.objects.filter(addr=addr):
                raise InexistantObjectError("The addresse \"" + addr
                    + "\" was not found in the database")
            else:
                if pool is None:
                    pool = models.Address.objects.get(addr=addr).pool

                addrobj = models.Address.objects.get(addr=addr)
                if addrobj.macaddr:
                    newaddr = models.Address(macaddr=addrobj.macaddr,
                        host=addrobj.host, allocated=False)
                    newaddr.save()

                LOGGER.info("Delete address " + str(addr) + " from pool "
                    + str(pool.name))
                pool.free(addr)
    elif hosts:
        for host in hosts:
            hostobj = models.Host.objects.get(name=host)
            # addresses are automatically deleted = considered as free
            addrs = []
            for addr in models.Address.objects.filter(host=hostobj):
                if addr.addr:
                    addrs.append(addr.addr)
            LOGGER.info("Delete host " + str(hostobj)
                + ", releasing addresses: " + ", ".join(addrs))
            hostobj.delete()
    elif pool:
        # addresses are automatically deleted
        LOGGER.info("Delete pool " + str(pool))
        pool.delete()


def modify(pools=None, host=None, category=None, address=None, mac=None,
        newname=None, alias=None, serial="", inventory="", duration=None,
        lastuse=None, nodns=False, comment="", clearalias=False):
    """Modify the name of an object in the database."""
    poolobjs = []
        
    if not alias:
        alias = []

    if pools:
        for pool in pools:
            poolobjs.append(get_pool(pool))
    hostobj = get_host(host)
    addrobj = None
    if models.Address.objects.filter(addr=address):
        addrobj = models.Address.objects.get(addr=address)

    if address and addrobj and (mac or duration or lastuse or comment):
        if mac:
            addrobj.macaddr = mac
            LOGGER.info("Modify address " + str(addrobj) + ": assign MAC "
                + mac)
        if duration:
            addrobj.duration = (datetime.datetime.now() +
                datetime.timedelta(days=duration))
            LOGGER.info("Modify address " + str(addrobj)
                + ": new duration untill: " + str(addrobj.duration))
        if lastuse:
            addrobj.lastuse = datetime.datetime.fromtimestamp(lastuse)
        if comment:
            addrobj.comment = comment
        addrobj.save()
    elif host and hostobj:
        if not (newname or mac or alias or serial or inventory
                or nodns or clearalias):
            raise MissingParameterError("Please provide the new name "
                + "or a new information for the host " + hostobj.name)
        if mac:
            addrs = hostobj.address_set.all()
            LOGGER.info("Assign new MAC address " + mac + " to host " + host)
            if addrs:
                addrs[0].macaddr = mac
            else:
                addrs = [models.Address(macaddr=mac, host=hostobj)]
            addrs[0].save()
        if serial:
            hostobj.serial = serial
            LOGGER.info("Changed host " + hostobj.name + ": new serial: "
                + serial)
            hostobj.save()
        if inventory:
            hostobj.inventory = inventory
            LOGGER.info("Changed host " + hostobj.name
                + ": new inventory number: " + inventory)
            hostobj.save()
        if newname:
            #anomalie de hostname avec espace
            if not isValidHostname(hostname=newname):
                raise PropertyFormatError(
                                          "You must provide a valid name (without space, special character) for the new host.")
        
            #anomalie9
            #verifier si le new hostname a le meme alias dans les nouveaux alias et ancienne liste de alias.
            #la nouvelle liste
            if alias:
                for alia in alias:
                    if alia[0] != '-' and alia[0] != '%':
                        if (alia == newname):
                            raise DuplicateObjectError("Host [" + newname + "] is the same as the new alias.")
                        
            #le nouveau hostname ne faut pas existe dans la liste de tous les alias de tous les host
            if models.Alias.objects.filter(name=newname):
                raise DuplicateObjectError("Host [" + newname + "] already exists in the list of alias.")
            #le nouveau hostname ne faut pas existe dans la liste tous les host    
            if models.Host.objects.filter(name=newname):
                raise DuplicateObjectError("Host [" + newname + "] already exists.")
            #fin anomalie9
            LOGGER.info("Changed name of host " + hostobj.name + " to " + newname)
            hostobj.name = newname
            hostobj.save()
        if category:
            category = category[0]
            LOGGER.info("Changed category of host " + hostobj.name + " to "
                + category)
            hostobj.category = category
            hostobj.save()
        if nodns:
            LOGGER.info("Changed NODNS setting of host " + hostobj.name)
            hostobj.nodns = not hostobj.nodns
            hostobj.save()
        if clearalias:
            models.Alias.objects.filter(host=hostobj).delete()
            LOGGER.info("Cleared all aliases for host " + host)
        elif alias:
            for alia in alias:
                # % was introduced because of argparse, which think some
                # argument beginning by - is an option...
                # http://bugs.python.org/issue9334
                if alia[0] == '-' or alia[0] == '%':
                    alia = alia[1:]
                    if models.Alias.objects.filter(name=alia, host=hostobj):
                        models.Alias.objects.filter(name=alia,
                            host=hostobj).delete()
                        LOGGER.info("Deleted alias \"" + alia + "\" for host "
                            + host)
                else:
                    if not isValidHostname(hostname=alia):
                        raise PropertyFormatError(
                                          "You must provide a valid name (without space, special character) for the new host.")
                    #le nouveau alias exist pas dans la liste de alias 
                    if models.Alias.objects.filter(name=alia):
                        raise DuplicateObjectError("Alias [" + alia + "] already exists.")
                    #anomalie9
                    #le nouveau alias exist pas dans la liste de host
                    elif models.Host.objects.filter(name=alia):
                        raise DuplicateObjectError("Host already exists as alias ["  + alia + "]")
                    #le nouveau alias n'est pas identique que le nouveau hostname
                    elif newname and (alia == newname):
                        raise DuplicateObjectError("The new alias [" + alia + "] is the same as the new host name.")
                    #fin anomalie9
                    else:
                        LOGGER.info("New alias " + alia + " for host " + host)
                        aliasobj = models.Alias(name=alia, host=hostobj)
                        aliasobj.save()
    elif pools and poolobjs:
        poolobj = poolobjs[0]
        if not category and not newname:
            raise MissingParameterError("Please provide the new name or a "
                + "category for the pool " + poolobj.name)
        if category:
            category = ",".join(category)
            LOGGER.info("Changed category of pool " + poolobj.name + " to "
                + category)
            poolobj.category = category
        if newname:
            LOGGER.info("Changed namme of pool " + poolobj.name + " to "
                + newname)
            poolobj.name = newname
        poolobj.save()
    else:
        raise InexistantObjectError(
            "Could not find the object to modify or wrong action.")


def quick_set_prop(prop=None, pool=None, host=None, del_=False):
    """Parse the property set format value=key and set the property."""
    if del_:
        set_prop(prop, None, pool, host, del_)
    else:
        if prop.find("=") < 0:
            raise PropertyFormatError("Property format is property=value.")
        prop_name = prop[:prop.find("=")]
        prop_value = prop[prop.find("=") + 1:]
        set_prop(prop_name, prop_value, pool, host, del_)


def set_prop(name=None, value=None, pool=None, host=None, del_=False):
    """Set or change a property."""
    hostobj = None
    poolobj = None

    if host is not None:
        hostobj = get_host(host)
        if del_:
            LOGGER.info("Deleted property " + name + " of host " + str(host))
        else:
            LOGGER.info("Changed property " + name + " of host " + str(host) +
                " to " + value)
    elif pool is not None:
        poolobj = get_pool(pool)
        if del_:
            LOGGER.info("Deleted property " + name + " of pool " + pool)
        else:
            LOGGER.info("Changed property " + name + " of pool " + pool
                + " to " + value)
    else:
        raise MissingParameterError(
            "You must specify a pool or a host name to set the property of.")

    if poolobj is None:
        props = models.Property.objects.filter(host=hostobj)
    else:
        props = models.Property.objects.filter(pool=poolobj)

    if del_:
        if props.filter(name=name):
            props.get(name=name).delete()
        else:
            raise InexistantObjectError("Could not find property: " + name)
    else:
        if props.filter(name=name):
            prop_obj = props.get(name=name)
            prop_obj.value = value
        else:
            prop_obj = models.Property(name=name, value=value,
                host=hostobj, pool=poolobj)
        prop_obj.save()


def sort_addresses(addrs):
    """Sort addresses given as argument in place, all addresses must belong to
    the same pool."""
    if not addrs or not addrs[0].pool:
        return addrs
    if not addrs[0].pool.addr_range:
        addrs[0].pool._update()
    sortablefunc = addrs[0].pool.addr_range.sortable
    return sorted(addrs, key=sortablefunc)


def set_log_author(author):
    """Set name of the user for logging."""
    DBLOGHANDLER.author = author


def delete_logs(days=0):
    """Delete log entries older than *date*."""
    if days != 0:
        models.LogEntry.objects.filter(date__lt=datetime.datetime.now()
            - datetime.timedelta(days=days)).delete()

def export(cmd):
    """Export SLAM's command allowing to recreate the current database from
    scratch."""
    res = ""
    for pool in models.Pool.objects.all():
        option = ""
        if pool.addr_range_str:
            option += " -p " + pool.addr_range_str
        if pool.category:
            option += " -c " + pool.category
        res += cmd + " -a create -pn " + pool.name + option + "\n"

    allocated = []
    for host in models.Host.objects.all():
        option = ""
        if host.category:
            option += " -c " + host.category
        if host.serial:
            option += " --serial " + host.serial
        if host.inventory:
            option += " --inventory " + host.inventory
        for alias in models.Alias.objects.filter(host=host):
            option += " --alias " + alias.name
        for addr in models.Address.objects.filter(host=host):
            if addr.addr:
                option += " -A " + addr.addr
                allocated.append(addr.addr)
                break
        res += cmd + " -a create -H " + host.name + option + "\n"

    for prop in models.Property.objects.all():
        option = ""
        if prop.pool:
            option += " -pn " + prop.pool.name
        elif prop.host:
            option += " -H " + prop.host.name
        res += (cmd + " -a setprop " + prop.name + "=" + prop.value
            + option + "\n")

    for addr in models.Address.objects.all():
        if addr.macaddr and addr.host:
            res += (cmd + " -a modify -H " + addr.host.name
                + " -m " + addr.macaddr + "\n")

        if not addr.addr:
            continue

        option = ""
        if addr.host:
            option += " -H " + addr.host.name
        if addr.pool:
            option += " -pn " + addr.pool.name
        if addr.duration:
            option += " --duration " + int(
                addr.duration - datetime.datetime.now().total_seconds())
        if addr.lastuse:
            option += " --last-use " + addr.lastuse.strftime("%s")

        if addr.addr in allocated:
            if addr.duration or addr.lastuse:
                res += cmd + " -a modify -A " + addr.addr + option + "\n"
        elif not addr.host:
            res += cmd + " -a create -A " + addr.addr + option + "\n"
        else:
            res += cmd + " -a get -A " + addr.addr + option + "\n"

    for gen in models.Config.objects.all():
        type_ = ""
        if not gen.conftype:
            continue
        if gen.conftype == "bind":
            type_ = "bind"
        elif gen.conftype == "rbind":
            type_ = "revbind"
        elif gen.conftype == "dhcp":
            type_ = "dhcp"
        elif gen.conftype == "quatt":
            type_ = "quattor"
        elif gen.conftype == "laldns":
            type_ = "laldns"
        else:
            continue

        option = ""
        if gen.default:
            option += "--default"
        if gen.outputfile:
            option += " -o " + gen.outputfile
        if gen.headerfile:
            for head in gen.headerfile.split(","):
                option += " --header " + head
        if gen.footerfile:
            for foot in gen.footerfile.split(","):
                option += " --footer " + foot
        if gen.checkfile:
            for check in gen.checkfile.split(","):
                option += " --checkfile " + check
        if gen.timeout:
            option += " --timeout " + gen.timeout
        if gen.domain:
            option += " --domain " + gen.domain
        res += cmd + " -a create " + type_ + "\n"

    return res
