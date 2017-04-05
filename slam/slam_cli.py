#!/usr/bin/env python

"""Command-line interface for SLAM."""

import os, pwd, sys, argparse, logging, signal

os.environ["DJANGO_SETTINGS_MODULE"] = "webinterface.settings"

from slam import models, interface, addrrange, generator

def init_argparser():
    """Initialize the SLAM argparser."""
    argparser = argparse.ArgumentParser(
        description= "SLAM command-line interface")
    argparser.add_argument("-a", "--action", action="append", required=True,
        choices=["list", "create", "get", "delete", "modify", "setprop",
            "rmprop", "createconf", "upconf", "log", "export"],
        help="The action to perform: list | create | get | delete | modify "
            + "| setprop | rmprop | createconf | upconf | export")
    argparser.add_argument("-pn", "--pool-name", action="append",
        help="The name of an address pool.")
    argparser.add_argument("-c", "--category", action="append",
        help="The category of an address pool.")
    argparser.add_argument("-p", "--pool",
        help="Address definition of the pool to manage "
            + "(ex: 10.1.2.0/24, fc00::/7, \"addr1,addr2,addr3\").")
    argparser.add_argument("-A", "--address", action="append",
        help= "An address to list, allocate or free.")
    argparser.add_argument("-m", "--mac", action="append",
        help= "A mac-address to bind to a host.")
    argparser.add_argument("-H", "--host", action="append",
        help="The name of the host to manage.")
    argparser.add_argument("-r", "--random", action="store_true",
        help="Hosts will get random addresses from the pool.")
    argparser.add_argument("-g", "--generator", action="store",
        help="Name of the configuration generator.")
    argparser.add_argument("-o", "--output", action="store",
        help="Output file path for the configuration files to generate, "
            + "or - for stdout.")
    argparser.add_argument("--default", action="store_true",
        help="Set the generator as default or toogle its state.")
    argparser.add_argument("--header", action="store",
        help="Header file path for the configuration files to generate.")
    argparser.add_argument("--footer", action="store",
        help="Footer file path for the configuration files to generate.")
    argparser.add_argument("--checkfile", action="append",
        help="Files to scan for duplicates while generating configuration.")
    argparser.add_argument("--timeout", action="store",
        help="Timeout for the generated configuration (ie: bind...).")
    argparser.add_argument("--domain", action="store",
        help="Domain for the hosts to generate.")
    argparser.add_argument("--alias", action="append",
        help="An alias for a host name")
    argparser.add_argument("--inventory", action="store",
        help="Inventory number for a host")
    argparser.add_argument("--serial", action="store",
        help="Serial number of a machine.")
    argparser.add_argument("--duration", action="store",
        help="Number of day for a temporary allocation.")
    argparser.add_argument("--lastuse", action="store",
        help="UNIX timestamp of the last use of the address.")
    argparser.add_argument("--comment", action="store",
        help="Store a comment related to an address.")
    argparser.add_argument("--nodns", action="store_true",
        help="No DNS record will be generated for the addresses of this host.")
    argparser.add_argument("extra", metavar="ARG", nargs="*",
        help="Extra arguments required by specific actions (ie: modify).")

    return argparser


def parse_args(argparser, argv):
    """Define available arguments and parse the command-line."""
    args = argparser.parse_args(argv)
    # We have to accept a list of option, to write an error message in case
    # there are several -a or -pn, otherwise, they get overwritten quietly.
    if args.action:
        if len(args.action) == 0 or len(args.action) > 1:
            logging.error("Please provide one --action argument.")
            sys.exit(1)
        args.action = args.action[0]

    if args.duration:
        args.duration = int(args.duration)
    if args.lastuse:
        args.lastuse = int(args.lastuse)

    if args.alias:
        realalias = []
        for alia in args.alias:
            realalias.extend(alia.split(","))
        args.alias = realalias

    return args


def generate(args):
    """Generate a configuration file from the host in the database."""
    if not args.extra:
        args.extra = [None]

    try:
        duplicates = interface.generate(gen_name=args.generator,
            pool_name=args.pool_name, conf_format=args.extra[0],
            output=args.output, header=args.header, footer=args.footer,
            checkfile=args.checkfile, timeout=args.timeout, domain=args.domain,
            update=(args.action=="upconf"))
    except (IOError, interface.InexistantObjectError,
            interface.ConfigurationFormatError,
            generator.DuplicateRecordError) as exc:
        logging.error(str(exc))
        sys.exit(1)

    for dup_host, dup_file, dup_line in duplicates:
        logging.warn("Duplicate record: a record already exists for host "
            + str(dup_host) +  " in file " + dup_file + " at line "
            + str(dup_line))


def _list_props(args):
    """Filter listed objects by properties."""
    for prop in args.extra:
        if "=" in prop:
            idx = prop.find("=")
            prop_name = prop[:idx]
            prop_value = prop[idx + 1:]
            for pool in models.Pool.objects.filter(
                    property__name=prop_name, property__value=prop_value):
                print "Pool: " + str(pool)
            for host in models.Host.objects.filter(
                    property__name=prop_name, property__value=prop_value):
                print "Host: " + str(host)
        else:
            for pool in models.Pool.objects.filter(property__name=prop):
                print "Pool: " + str(pool)
            for host in models.Host.objects.filter(property__name=prop):
                print "Host: " + str(host)


def _list_hosts(args):
    """List all the hosts in the database."""
    for host in args.host:
        if host:
            try:
                hostobj = interface.get_host(host)
            except interface.InexistantObjectError:
                logging.error("Could not find a host name: " + host)
                sys.exit(1)

            # mac address(es)
            hoststr = str(hostobj)
            if models.Address.objects.filter(host=hostobj).exclude(macaddr=""):
                hoststr = hoststr + ", mac: "
                for addrobj in models.Address.objects.filter(
                        host=hostobj).exclude(macaddr=""):
                    hoststr = hoststr + addrobj.macaddr + ", "
                hoststr = hoststr[:-2] # strip the last comma

            print "Host " + hoststr
            if hostobj.serial:
                print("Serial number: " + hostobj.serial)
            if hostobj.inventory:
                print("Inventory number: " + hostobj.inventory)
            if hostobj.category:
                print("Category: " + hostobj.category)
            if hostobj.alias_set.count() > 0:
                print("Alias: " + ", ".join(
                    [alias.name for alias in list(hostobj.alias_set.all())]))
            if hostobj.nodns:
                print("NODNS")
            for addr in models.Address.objects.filter(host=hostobj).exclude(
                    addr="").order_by("addr"):
                if addr.pool:
                    print ("Address " + str(addr) + " (pool: " +
                        addr.pool.name + ")")
                else:
                    print "Address " + str(addr)
            for prop in models.Property.objects.filter(host=hostobj):
                print str(prop)
        else:
            for hostobj in models.Host.objects.all().order_by("name"):
                msg = str(hostobj)
                if hostobj.alias_set.all():
                    msg += " (" + ", ".join([str(alias) for alias
                        in hostobj.alias_set.all()]) + ")"
                if hostobj.category:
                    msg += ", category: " + hostobj.category
                for addr in hostobj.address_set.all():
                    msg += ", " + str(addr)
                print(msg)


def _list_generator(args):
    """List all the Generator objects from the database."""
    if args.generator:
        try:
            gen = interface.get_generator(args.generator)
        except interface.InexistantObjectError as exc:
            logging.error(str(exc))
            sys.exit(1)

        if gen.default:
            print (gen.conftype + " generator: " + gen.name + ", default")
        else:
            print (gen.conftype + " generator: " + gen.name)

        print ("  output file: \"" + gen.outputfile + "\"")
        if gen.pool_set.all():
            print ("  pools: \"" + ", ".join(
                [pool.name for pool in gen.pool_set.all()]) + "\"")
        if gen.headerfile:
            print ("  header file: \"" + gen.headerfile + "\"")
        if gen.footerfile:
            print ("  footer file: \"" + gen.footerfile + "\"")
        if gen.checkfile:
            print ("  check files: \"" + gen.checkfile + "\"")
    else:
        for gen in models.Config.objects.all().order_by("name"):
            print str(gen)


def list_(args):
    """List objects in the database."""
    if args.pool_name and len(args.pool_name) > 1:
        logging.error("Please specify only one pool name.")
        sys.exit(1)

    if args.pool_name:
        try:
            pool = interface.get_pool(args.pool_name[0])
        except interface.InexistantObjectError as exc:
            logging.error(str(exc))
            sys.exit(1)

        used = models.Address.objects.filter(pool=pool).count()
        tot = pool.len()
        print("Pool: " + str(pool) + ", " + str(used) + "/" + str(tot)
            + " (" + str(used * 100 / tot) + "%)")
        if pool.category:
            print("Categories: " + ", ".join(pool.category.split(",")))
        addrs = list(models.Address.objects.filter(pool=pool))
        addrs = interface.sort_addresses(addrs)
        for addr in addrs:
            print str(addr) + "\t\t" + str(addr.host)
        for prop in models.Property.objects.filter(pool=pool).order_by("name"):
            print str(prop)
    elif args.address:
        for addrstr in args.address:
            addrs = models.Address.objects.filter(addr=addrstr)
            if not addrs.count():
                logging.error("Could not find the address: " + addrstr)
                sys.exit(1)
            for addr in addrs:
                print "Address: " + str(addr)
                if addr.pool:
                    print("\tPool: " + str(addr.pool))
                if addr.host:
                    print("\tHost: " + str(addr.host))
                if addr.duration:
                    print("\tTemporary until: " + str(addr.duration))
                if addr.comment:
                    print("\tComment:\n" + addr.comment)
    elif args.host:
        _list_hosts(args)
    #filter by property
    elif args.extra and len(args.extra) > 0:
        _list_props(args)
    elif args.generator is not None:
        _list_generator(args)
    else:
        print "Address pools:"
        for pool in models.Pool.objects.all().order_by("name"):
            print str(pool)


def get(args):
    """Get new address from pool."""
    pool = None
    if args.pool_name:
        try:
            pool = interface.get_pool(args.pool_name[0])
        except (interface.InexistantObjectError,
                interface.DuplicateObjectError) as exc:
            logging.error(str(exc))
            sys.exit(1)

    if args.host:
        for host in args.host:
            try:
                hostobj = interface.get_host(host)
            except interface.InexistantObjectError as exc:
                logging.error(str(exc))
                sys.exit(1)

            addr = None
            if not args.address:
                args.address = [None]
            try:
                if args.category:
                    args.category = args.category[0]
                addr = interface.allocate_address(pool, hostobj,
                    args.address[0], args.random, args.category, args.duration)
                del args.address[0]
            except (interface.MissingParameterError,
                    models.FullPoolError) as exc:
                logging.error(str(exc))
            except (models.AddressNotInPoolError,
                    models.AddressNotAvailableError) as exc:
                logging.warn(str(exc))

            if addr:
                print("Assigned " + str(addr) + " to host " + host)
    else:
        logging.error("Missing host to allocate address to.")
        sys.exit(1)


def _create_host(args, pool):
    """Create hosts given as arguments."""
    for host in args.host:
        if not args.address:
            args.address = [None]
        if not args.category:
            args.category = [None]

        if args.mac:
            macaddr = args.mac[0]
            del args.mac[0]
        else:
            macaddr = None
        try:
            hostres, addrres = interface.create_host(host, pool,
                args.address[0], macaddr, args.random, args.alias,
                args.category[0], args.serial, args.inventory, args.duration,
                args.nodns)
            if addrres is None:
                print ("Host \"" + hostres + "\" have been created.")
            else:
                print("Assigned " + addrres + " to host " + hostres)
        except (models.AddressNotInPoolError,
                models.AddressNotAvailableError,
                models.FullPoolError,
                interface.DuplicateObjectError) as exc:
            logging.error(str(exc))
            sys.exit(1)
        del args.address[0]


def create(args):
    """Create a new object."""
    pool = []
    if (args.host or args.address or args.generator) and args.pool_name:
        try:
            for pool_name in args.pool_name:
                pool.append(interface.get_pool(pool_name))
        except interface.InexistantObjectError as exc:
            logging.error(str(exc))
            sys.exit(1)

    if not args.generator and not args.extra and not pool:
        pool = [None]

    # generator creation
    if args.generator and args.extra:
        if not args.pool_name:
            args.pool_name = []
        try:
            interface.create_generator(args.generator, args.extra[0],
                args.output, args.default, args.header, args.footer,
                args.checkfile, args.timeout, args.domain, args.pool_name)
        except (interface.DuplicateObjectError,
                interface.MissingParameterError) as exc:
            logging.error(str(exc))
            sys.exit(1)
    else:
        if pool and len(pool) > 1:
            logging.error("Please specify only one pool name.")
            sys.exit(1)
        if args.pool_name and (args.host or args.address):
            pool = interface.get_pool(args.pool_name[0])
        else:
            pool = None

        # host creation
        if args.host:
            _create_host(args, pool)
        # stand-alone addresses creation
        elif args.address:
            for addr in args.address:
                try:
                    interface.allocate_address(pool, address=addr)
                    print(addr + " has been allocated")
                except (models.AddressNotInPoolError,
                        models.AddressNotAvailableError) as exc:
                    logging.warn(str(exc))
        # pool creation
        elif args.pool_name:
            if pool is None:
                try:
                    pool = interface.create_pool(args.pool_name[0], args.pool,
                        args.category)
                except (addrrange.InvalidAddressError,
                        interface.MissingParameterError) as exc:
                    logging.error(str(exc))
                    sys.exit(1)
            else:
                logging.error("Pool already exists :" + args.pool_name[0])
                sys.exit(1)
        else:
            logging.error("Missing parameters for object creation.")
            sys.exit(1)


def delete(args):
    """Delete an object from the database."""
    if args.generator:
        try:
            interface.get_generator(args.generator)
        except interface.InexistantObjectError as exc:
            logging.error(str(exc))
            sys.exit(1)
        print("Removed generator \"" + args.generator + "\".")
        models.Config.objects.filter(name=args.generator).delete()
    else:
        pool = None
        if args.pool_name:
            try:
                pool = interface.get_pool(args.pool_name[0])
            except interface.InexistantObjectError as exc:
                logging.error(str(exc))
                sys.exit(1)

        try:
            interface.delete(pool, args.address, args.host)
        except (interface.InexistantObjectError, models.AddressNotInPoolError,
                models.AddressNotAllocatedError) as exc:
            logging.error(str(exc))
            sys.exit(1)


def modify(args):
    """Modify a given property of an object."""
    # argparse is made so we need lists for these arguments, but
    # interface.modify wants atom arguments, so in case of None arguments, we
    # insert an array containing None to avoid crashing on the call to
    # interface.modify
    if not args.host:
        args.host = [None]
    if not args.address:
        args.address = [None]
    if not args.extra:
        args.extra = [None]
    if not args.mac:
        args.mac = [None]

    try:
        if args.generator:
            interface.modify_generator(args.generator, args.default,
                args.output, args.header, args.footer, args.checkfile,
                args.timeout, args.domain, args.pool_name)
        else:
            clearalias = (args.alias and len(args.alias) == 1
                and len(args.alias[0]) == 0)
            interface.modify(args.pool_name, args.host[0], args.category,
                args.address[0], args.mac[0], args.extra[0], args.alias,
                args.serial, args.inventory, args.duration, args.lastuse,
                args.nodns, args.comment, clearalias=clearalias)
    except (interface.InexistantObjectError,
            interface.MissingParameterError) as exc:
        logging.error(str(exc))
        sys.exit(1)


def set_(args):
    """Set a given property on an object."""
    if not args.pool_name:
        args.pool_name = [None]

    if not args.host or len(args.host) == 0:
        args.host = [None]
    try:
        for prop in args.extra:
            interface.quick_set_prop(prop, args.pool_name[0],
                args.host[0], args.action == "rmprop")
            if args.action == "rmprop":
                print("Removed " + prop)
            else:
                print(prop)
    except (interface.PropertyFormatError, interface.MissingParameterError,
            interface.InexistantObjectError) as exc:
        logging.error(str(exc))
        sys.exit(1)


def list_logs(args):
    """View log entries."""
    for entry in models.LogEntry.objects.all().order_by("date"):
        print(str(entry))


def authenticate():
    """Check the system user list for authorized users."""
    allowed = []
    if os.access("/etc/slam/users", os.R_OK):
        accessf = open("/etc/slam/users")
        allowed = accessf.read().split("\n")
        accessf.close()
    if not allowed:
        allowed = ["root"]
    return pwd.getpwuid(os.getuid())[0] in allowed


def run_cli():
    """Dispatch the command-line commands to the different handling
    functions."""
    # Terminate on broken pipes
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    if not authenticate():
        sys.stderr.write("You are not on the authorized users' list, "
            "ask your system administrator to allow your username.\n")
        sys.exit(1)

    argparser = init_argparser()
    cmd = sys.argv[0]
    del sys.argv[0]
    args = parse_args(argparser, sys.argv)
    if not args.action:
        argparser.print_help()
        sys.exit(1)

    if args.action == "setprop" or args.action == "rmprop":
        set_(args)
    elif args.action == "createconf" or args.action == "upconf":
        generate(args)
    elif args.action == "create":
        create(args)
    elif args.action == "get":
        get(args)
    elif args.action == "delete":
        delete(args)
    elif args.action == "modify":
        modify(args)
    elif args.action == "log":
        list_logs(args)
    elif args.action == "export":
        print(interface.export(cmd))
    else: # "list"
        list_(args)


if __name__ == "__main__":
    run_cli()
