""" Test module for the command-line interface of SLAM.

It imports the differents functions used by the CLI and call them directly with
various arguments simulating a call from a shell.

Note: This module decrease the logging level to minimize the message flow to
the console during the test. It also replaces stdout by a StringIO which enable
the capture of stdout in a string and allows us to compare it to a reference
output.
"""

import os
import sys
import argparse
import StringIO
import logging
from nose.tools import assert_raises
from slam.models import Pool, Host, Address, Property
from slam import generator

import slam_cli

def setup():
    logging.basicConfig(level=logging.CRITICAL)

def test_parse_args():
    ap = slam_cli.init_argparser()

    ns = slam_cli.parse_args(ap, "-a list".split())
    assert ns.action == "list"

    assert not ns.random
    ns = slam_cli.parse_args(ap, "-a create -pn foo -r -H slamserver".split())
    assert ns.random

    assert_raises(SystemExit, slam_cli.parse_args, ap, "".split())
    assert_raises(SystemExit, slam_cli.parse_args, ap,
        "--action list -a delete".split())
    assert_raises(SystemExit, slam_cli.parse_args, ap, "-a wrong".split())
    assert_raises(SystemExit, slam_cli.parse_args, ap,
        "-a list -a create".split())
    assert_raises(SystemExit, slam_cli.parse_args, ap, "--po poolname".split())
    assert_raises(SystemExit, slam_cli.parse_args, ap,
        "-pn poolname -pn bar".split())


def test_list():
    saved_out = sys.stdout
    ap = slam_cli.init_argparser()

    args = slam_cli.parse_args(ap, "-a list -pn inexistant".split())
    assert_raises(SystemExit, slam_cli.list_, args)
    args = slam_cli.parse_args(ap, "-a list -H inexistant".split())
    assert_raises(SystemExit, slam_cli.list_, args)
    args = slam_cli.parse_args(ap, "-a list -A inexistant".split())
    assert_raises(SystemExit, slam_cli.list_, args)

    args = slam_cli.parse_args(ap,
        "-a create -pn test1 -p 192.168.0.0/16".split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap, ("-a create -H host1 -pn test1 -m mac-1 "
        + "--alias alias1 --alias alias2 --serial srlnm "
        + "--inventory invnum").split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap, "-a list".split())
    slam_cli.list_(args)

    sys.stdout = StringIO.StringIO()
    args = slam_cli.parse_args(ap, "-a list -pn test1".split())
    slam_cli.list_(args)
    assert(sys.stdout.getvalue() ==
        'Pool: test1 (range: 192.168.0.0/16), 1/65536 (0%)\n' +
        '192.168.0.0\t\thost1\n')

    sys.stdout = StringIO.StringIO()
    args = slam_cli.parse_args(ap, "-a list -H host1".split())
    slam_cli.list_(args)
    assert(sys.stdout.getvalue() == 'Host host1, mac: mac-1'
        + '\nSerial number: srlnm\nInventory number: invnum\n'
        + 'Alias: alias1, alias2\nAddress 192.168.0.0 (pool: test1)\n')

    sys.stdout = StringIO.StringIO()
    args = slam_cli.parse_args(ap, "-a list -A 192.168.0.0".split())
    slam_cli.list_(args)
    assert(sys.stdout.getvalue() ==
        'Address: 192.168.0.0\n'
        + '\tPool: test1 (range: 192.168.0.0/16)\n'
        + '\tHost: host1\n')

    args = slam_cli.parse_args(ap, "-a setprop -pn test1 building=200".split())
    slam_cli.set_(args)
    args = slam_cli.parse_args(ap, "-a setprop -H host1 building=333".split())
    slam_cli.set_(args)
    sys.stdout = StringIO.StringIO()
    args = slam_cli.parse_args(ap, "-a list building".split())
    slam_cli.list_(args)
    args = slam_cli.parse_args(ap, "-a list building=333".split())
    slam_cli.list_(args)
    args = slam_cli.parse_args(ap, "-a list building=200".split())
    slam_cli.list_(args)
    assert(sys.stdout.getvalue() ==
        "Pool: test1 (range: 192.168.0.0/16)\n"
        + "Host: host1\n"
        + "Host: host1\n"
        + "Pool: test1 (range: 192.168.0.0/16)\n")

    args = slam_cli.parse_args(ap, "-a create -g quatgen -o - quattor".split())
    slam_cli.create(args)
    arglist = "-a list -g".split()
    arglist.append("")
    args = slam_cli.parse_args(ap, arglist)
    sys.stdout = StringIO.StringIO()
    slam_cli.list_(args)
    assert(sys.stdout.getvalue() ==
        "quatgen (quatt), output file: \"-\"\n")

    sys.stdout = saved_out


def test_list_generator():
    saved_out = sys.stdout
    ap = slam_cli.init_argparser()
    generator.Config.objects.all().delete()

    args = slam_cli.parse_args(ap, "-a create -g bindgen bind -o -".split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap,
        ("-a create -g quatgen quattor -o /tmp/out --header hdr --footer ftr "
        + "--checkfile checkf1 --checkfile checkf2").split())
    slam_cli.create(args)

    sys.stdout = StringIO.StringIO()
    args = slam_cli.parse_args(ap, "-a list -g quatgen".split())
    slam_cli.list_(args)
    assert(sys.stdout.getvalue() == "quatt generator: quatgen\n"
        + '  output file: "/tmp/out"\n'
        + '  header file: "hdr"\n'
        + '  footer file: "ftr"\n'
        + '  check files: "checkf1, checkf2"\n')

    sys.stdout = StringIO.StringIO()
    arglist = "-a list -g".split()
    arglist.append("")
    args = slam_cli.parse_args(ap, arglist)
    slam_cli.list_(args)
    assert(sys.stdout.getvalue() == "bindgen (bind), output file: \"-\"\n"
        + "quatgen (quatt), output file: \"/tmp/out\"\n")

    sys.stdout = saved_out


def test_create():
    ap = slam_cli.init_argparser()

    args = slam_cli.parse_args(ap,
        "-a create -pn inexistant -H hostrandom".split())
    assert_raises(SystemExit, slam_cli.create, args)
    args = slam_cli.parse_args(ap, "-a create -pn testfail -p 192.168".split())
    assert_raises(SystemExit, slam_cli.create, args)

    args = slam_cli.parse_args(ap, "-a create -H newhost".split())
    slam_cli.create(args)
    assert Host.objects.filter(name="newhost").count() == 1
    args = slam_cli.parse_args(ap, "-a create -pn test2 -p 10.0.0.0/8".split())
    slam_cli.create(args)
    assert Pool.objects.filter(name="test2").count() == 1
    args = slam_cli.parse_args(ap, "-a create -H host2 -pn test2".split())
    slam_cli.create(args)
    assert Address.objects.filter(host__name="host2").count() == 1
    args = slam_cli.parse_args(ap,
        "-a get -H host2 -pn test2 -A 10.50.50.50".split())
    slam_cli.get(args)
    assert Address.objects.filter(host__name="host2").count() == 2
    args = slam_cli.parse_args(ap, "-a get -H host2 -pn test2".split())
    slam_cli.get(args)
    assert Address.objects.filter(host__name="host2").count() == 3

    assert Address.objects.filter(addr="10.100.10.100").count() == 0
    args = slam_cli.parse_args(ap,
        "-a create -pn test2 -A 10.100.10.100".split())
    slam_cli.create(args)
    assert Address.objects.filter(addr="10.100.10.100").count() == 1

    args = slam_cli.parse_args(ap,
        "-a create -pn testcat -p 4.5.0.0/16 -c server".split())
    slam_cli.create(args)
    assert Pool.objects.filter(category="server").count() == 1
    args = slam_cli.parse_args(ap, "-a create -H hostcat -c server".split())
    slam_cli.create(args)
    assert Address.objects.get(host__name="hostcat").pool.category == "server"

    args = slam_cli.parse_args(ap, "-a get -pn inexistant".split())
    assert_raises(SystemExit, slam_cli.create, args)
    args = slam_cli.parse_args(ap, "-a get".split())
    assert_raises(SystemExit, slam_cli.create, args)


def test_delete():
    ap = slam_cli.init_argparser()

    args = slam_cli.parse_args(ap, "-a delete -pn inexistant".split())
    assert_raises(SystemExit, slam_cli.delete, args)

    return
    args = slam_cli.parse_args(ap,
        "-a create -pn test3 -p 172.16.0.0/12".split())
    slam_cli.create(args)
    assert Pool.objects.filter(name="test3").count() == 1
    args = slam_cli.parse_args(ap, "-a delete -pn test3".split())
    slam_cli.delete(args)
    assert Pool.objects.filter(name="test3").count() == 0

    args = slam_cli.parse_args(ap,
        "-a create -pn test3 -p 172.16.0.0/12".split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap, "-a create -pn test3 -A 172.16.0.3".split())
    slam_cli.create(args)
    assert Address.objects.filter(addr="172.16.0.3").count() == 1
    args = slam_cli.parse_args(ap, "-a delete -pn test3 -A 172.16.0.3".split())
    slam_cli.delete(args)
    assert Address.objects.filter(addr="172.16.0.3").count() == 0

    args = slam_cli.parse_args(ap, "-a create -pn test3 -H host3-1".split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap, "-a get -pn test3 -H host3-1".split())
    slam_cli.create(args)
    assert Address.objects.filter(pool__name="test3").count() == 2
    args = slam_cli.parse_args(ap, "-a delete -pn test3 -H host3-1".split())
    slam_cli.delete(args)
    assert Address.objects.filter(pool__name="test3").count() == 0


def test_generate():
    saved_out = sys.stdout
    ap = slam_cli.init_argparser()

    args = slam_cli.parse_args(ap, "-a createconf -pn inexistant".split())
    assert_raises(SystemExit, slam_cli.generate, args)

    args = slam_cli.parse_args(ap, "-a create -pn test4 -p 1.2.3.0/24".split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap,
        "-a create -pn test4 -H host4-1 -H host4-2".split())
    slam_cli.create(args)
    sys.stdout = StringIO.StringIO()
    args = slam_cli.parse_args(ap, "-a createconf -pn test4 bind -o -".split())
    slam_cli.generate(args)

    saved_out.write("@@@@" + sys.stdout.getvalue() + "@@@")
    assert(sys.stdout.getvalue() ==
        "\n; This section will be automatically generated by SLAM any manual "
        + "change will\n; be overwritten on the next generation of this "
        + "file.\n; Pool test4 (range: 1.2.3.0/24)\n"
        + "host4-1\t1D\tIN\tA\t1.2.3.0\n"
        + "host4-2\t1D\tIN\tA\t1.2.3.1\n"
        + "; END of section automatically generated by SLAM\n")

    args = slam_cli.parse_args(ap, "-a createconf bind -o /tmp".split())
    assert_raises(SystemExit, slam_cli.generate, args)

    sys.stdout = saved_out


def test_modify():
    ap = slam_cli.init_argparser()

    args = slam_cli.parse_args(ap,
        "-a create -pn modifytest1 -p fe80::/64".split())
    slam_cli.create(args)
    assert(Pool.objects.filter(name="modifytest1").count() == 1
        and Pool.objects.filter(name="modifytest2").count() == 0)
    args = slam_cli.parse_args(ap,
        "-a modify -pn modifytest1 modifytest2".split())
    slam_cli.modify(args)
    assert(Pool.objects.filter(name="modifytest1").count() == 0
        and Pool.objects.filter(name="modifytest2").count() == 1)

    args = slam_cli.parse_args(ap,
        "-a create -pn modifytest2 -H modifyhost1".split())
    slam_cli.create(args)
    assert(Host.objects.filter(name="modifyhost1").count() == 1
        and Host.objects.filter(name="modifyhost2").count() == 0)
    args = slam_cli.parse_args(ap,
        "-a modify -H modifyhost1 modifyhost2".split())
    slam_cli.modify(args)
    assert(Host.objects.filter(name="modifyhost1").count() == 0
        and Host.objects.filter(name="modifyhost2").count() == 1)

    args = slam_cli.parse_args(ap, "-a modify -H modifyhost2".split())
    assert_raises(SystemExit, slam_cli.modify, args)
    args = slam_cli.parse_args(ap, "-a modify -pn inexistant".split())
    assert_raises(SystemExit, slam_cli.modify, args)


def test_property():
    ap = slam_cli.init_argparser()

    args = slam_cli.parse_args(ap,
        "-a create -pn prop-pool -p 10.250.0.0/16".split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap,
        "-a setprop -pn prop-pool prop1=val1".split())
    slam_cli.set_(args)
    prop = Property.objects.get(pool__name="prop-pool", name="prop1")
    assert prop.value == "val1"
    args = slam_cli.parse_args(ap,
        "-a setprop -pn prop-pool prop1=val2".split())
    slam_cli.set_(args)
    prop = Property.objects.get(pool__name="prop-pool", name="prop1")
    assert str(prop) == "prop1: val2"

    args = slam_cli.parse_args(ap,
        "-a create -pn prop-pool -H hostprop".split())
    slam_cli.create(args)
    args = slam_cli.parse_args(ap, "-a setprop -H hostprop prop3=val3".split())
    slam_cli.set_(args)
    prop = Property.objects.get(host__name="hostprop", name="prop3")
    assert prop.value == "val3"
    args = slam_cli.parse_args(ap, "-a setprop -H hostprop prop3=val4".split())
    slam_cli.set_(args)
    prop = Property.objects.get(host__name="hostprop", name="prop3")
    assert prop.value == "val4"

    assert Property.objects.filter(host__name="hostprop").count() == 1
    args = slam_cli.parse_args(ap, "-a rmprop -H hostprop prop3".split())
    slam_cli.set_(args)
    assert Property.objects.filter(host__name="hostprop").count() == 0

    assert Property.objects.filter(pool__name="prop-pool").count() == 1
    args = slam_cli.parse_args(ap, "-a rmprop -pn prop-pool prop1".split())
    slam_cli.set_(args)
    assert Property.objects.filter(pool__name="prop-pool").count() == 0

    args = slam_cli.parse_args(ap, "-a rmprop foo".split())
    assert_raises(SystemExit, slam_cli.set_, args)
    args = slam_cli.parse_args(ap, "-a rmprop -pn inexistant foo".split())
    assert_raises(SystemExit, slam_cli.set_, args)
    args = slam_cli.parse_args(ap, "-a rmprop -H inexistant foo".split())
    assert_raises(SystemExit, slam_cli.set_, args)
    args = slam_cli.parse_args(ap, "-a setprop -H whatever foo".split())
    assert_raises(SystemExit, slam_cli.set_, args)
    args = slam_cli.parse_args(ap, "-a setprop -pn inexistant foo=bar".split())
    assert_raises(SystemExit, slam_cli.set_, args)
