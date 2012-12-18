Usage
=====

SLAM can be used through its Web interface or with a CLI script. Database is
centralised so both interfaces can be used at the same time.

Command-line interface
----------------------

Usage
^^^^^

::

    $ ./slam_cli.py
        [-h]
        -a {list|create|get|delete|modify|setprop|rmprop|createconf|upconf|doc}
        [-pn POOL_NAME]
        [-p POOL]
        [-A ADDRESS]
        [-H HOST]
        [-c CAT]
        [-m MAC]
        [--alias ALIAS]
        [-r]
        [-g GEN]
        [--default]
        [--header HDR]
        [--footer FTR]
        [-o OUTFILE]
        [--checkfile CHECK]
        [--timeout TIMEOUT]
        [--domain DOMAIN]
        [--inventory INVENTORY]
        [--serial SERIAL]
        [--duration DURATION]
        [--lastuse LASTUSE]
        [ARG...]

.. program:: slam-cli

.. option:: -h, --help

    Print the help message.

.. option:: -a, --action ACTION

    Select any available action among: list, create, get, delete,
    modify, setprop, rmprop, createconf, upconf or log.

    This option is required.

.. option:: -pn, --pool-name POOL_NAME

    The name of the address pool to apply actions onto.

.. option:: -p POOL, --pool POOL

     Address definition of the pool to manage (ex: 10.1.2.0/24, fc00::/7,
     "addr1,addr2,addr3").

.. option:: -A, --address ADDRESS

    An address to list, allocate or free.

.. option:: -H, --host HOST

    The name of the host to manage.

.. option:: -c, --category CAT

    One or more category of pool to create or to assign to a host.

.. option:: -m, --mac MAC

    The mac address to assign to the host.

.. option:: --alias ALIAS

    Specify one or more alias for the host name.

.. option:: -r, --random

    Hosts will get random addresses from the pool.

.. option:: -g , --generator GEN

    The name of a generator object to retrieve or create.

.. option:: --header HDR

    Header file path for the configuration files to generate. Its content will
    be inserted before the generated configuration.

.. option:: --footer FTR

    Footer file path for the configuration files to generate. Its content will
    be inserted after the generated configuration.

.. option:: -o, --output OUTFILE

    Output file path for the configuration files to generate, or - for stdout.

.. option:: --checkfile CHECK

    A list of file to check for duplicates before generating configuration.

.. option:: --timeout TIMEOUT

    A timeout in the format used by bind that will be used to generate records
    in bind files.

.. option:: --domain DOMAIN

    Specify a domain that will be used for every entry in the generated
    configuration files.

.. option:: --inventory INVENTORY

    Specify the inventory number of a host.

.. option:: --serial SERIAL

    Specify the serial number of a host.

.. option:: --duration DURATION

    Specify the duration of an address allocation, in days.

.. option:: --lastuse LASTUSE

    Update the time the address was last used with the new timestamp.

.. option:: ARG

    Specify arguments for additional information required by specific action or
    options like *generate* or *setprop*.

Examples
^^^^^^^^

List
""""

List all pools in the database::

    $ ./slam_cli.py -a list

List all addresses allocated in the pool *localnet*::

    $ ./slam_cli.py -a list -pn localnet

List all addresses allocated to the host *pc-42*::

    $ ./slam_cli.py -a list -H pc-42

Show which host the address *192.168.10.3* is allocated to and to which pool
it belongs::

    $ ./slam_cli.py -a list -A 192.168.10.3


Create
""""""

Create a new pool named *localnet* defined by the IPv4 subnet *10.9.8.0/24*::

    $ ./slam_cli.py -a create -pn localnet -p 10.9.8.0/24

Create a new host named *server4* and assign it a new available address from
*localnet*::

    $ ./slam_cli.py -a create -pn localnet -H server4

Mark the two given addresses from *localnet* as allocated but does not bind
them to a host::

    $ ./slam_cli.py -a create -pn localnet -A 10.9.8.0 -A 10.9.8.255

Specify the mac address and aliases of the new host::

    $ ./slam_cli.py -a create -pn localnet -H server5 -m 00:11:22:33:44:55 --alias webserver --alias mailserver

Create a pool *serv* of category *server* and *network*::

    $ ./slam_cli.py -a create -pn serv -p 1.2.3.0/24 -c server,network

Create a new host and assign it to the pool corresponding to the category
*server* (it will take an address from the *serv* pool::

    $ ./slam_cli.py -a create -H server64 -c server


Get
"""

Ask for a new address from *localnet* pool for the host *pc42*::

    $ ./slam_cli.py -a get -pn localnet -H pc42

Ask for a new address random from *localnet* pool for the host *pc42*::

    $ ./slam_cli.py -a get -pn localnet -H pc42 -r

Try to assign address *10.9.8.123* form pool to the host *pc42*::

    $ ./slam_cli.py -a get -pn localnet -H pc42 -A 10.9.8.123



Delete
""""""

Delete *localnet* and all the addresses it contained::

    $ ./slam_cli.py -a delete -pn localnet

Delete *server4* and mark all the addresses it had as unallocated::

    $ ./slam_cli.py -a delete -H server4

Unallocate *10.9.8.7*::

    $ ./slam_cli.py -a delete -A 10.9.8.7


Modify
""""""

Modify the name of a pool::

    $ ./slam_cli.py -a modify -pn localnet3 localnet30

Modify the name of a host, from "*pc-1337*" to "*server-1337*"::

    $ ./slam_cli.py -a modify -H pc-1337 server-1337

Modify the mac address of a host::

    $ ./slam_cli.py -a modify -H pc1337 -m 99:88:77:66:55:44

Modify the category of a pool::

    $ ./slam_cli.py -a modify -pn serv -c servercategory


Generate
""""""""

You can generate configuration entries in format for *Bind*, *Quattor* or
*DHCP*, simply specify **bind**, **revbind**, **quattor** or **dhcp** after the
generate.

Generate a configuration file for all hosts in the database::

    $ ./slam_cli.py -a createconf -o out.conf bind
    $ ./slam_cli.py -a createconf -o out.conf revbind
    $ ./slam_cli.py -a createconf -o out.conf quattor
    $ ./slam_cli.py -a createconf -o out.conf dhcp

Add additional paramters like timeout or domain::

    $ ./slam_cli.py -a createconf --timeout 3H -o out.conf bind
    $ ./slam_cli.py -a createconf --domain lan.example -o out.conf dhcp

Generate a DHCP configuration file for all hosts that have an address in
*localnet*::

    $ ./slam_cli.py -a createconf -pn localnet --domain lan.example -o out.conf dhcp

Add content before (*--header*) or after (*--footer*) the generated content::

    $ ./slam_cli.py -a createconf -pn localnet -o out.conf --header header.zonefile --footer footer.zonefile bind

Write the configuration output to stdout::

    $ ./slam_cli.py -a createconf -o - bind

Update an existing configuration file generated by SLAM::

    $ ./slam_cli.py -a upconf -o ./out.conf bind

Check for existing records in *conf.old1* and *conf.old2* before the generation
of the configuration::

    $ ./slam_cli.py -a createconf bind -o --checkfile conf.old1 --checkfile conf.old2

A *dhcpgen* generator object can be created this way::

    $ ./slam_cli.py -a create -g dhcpgen -o /etc/dhcpd/hosts.conf dhcp

It is possible to modify it::

    $ ./slam_cli.py -a modify -g dhcpgen --header /etc/dhcpd/header.conf

And then to use it instead of specifying every options::

    $ ./slam_cli.py -a createconf -g dhcpgen
    $ ./slam_cli.py -a updateconf -g dhcpgen

When creating a new generator it is possible to set as **default** for the
configuration type::

    $ ./slam_cli.py -a create -g dnsgen dns -o /etc/bind/db.foo.example --default

Then, whenever you run a *createconf* or *updateconf* without a generator name
or other options, it will run the generators that were set as **default**::

    $ ./slam_cli.py -a createconf
    $ ./slam_cli.py -a createconf dns

The second line will only run the default generators that generate DNS
configuration files.


Properties
""""""""""

Add a property to a pool object::

    $ ./slam_cli.py -a setprop -pn localnet building=200

Add a property to a host object::

    $ ./slam_cli.py -a setprop -H pc-1337 mac=00:12:34:56:78:9a

Change the property of an object::

    $ ./slam_cli.py -a setprop -H pc-1337 mac=00:42:42:42:42:42

Delete a given property of an object::

    $ ./slam_cli.py -a rmprop -H pc-1337 mac

List all pool and host that have a *building* property::

    $ ./slam_cli.py -a list building

List all pool and host that have a *buidling* property of value *200*::

    $ ./slam_cli.py -a list building=200


Logs
""""

Every action is logged in the database. It is possible to access log entries
with::

    $ ./slam_cli.py -a log


Web interface
-------------

Running a server
^^^^^^^^^^^^^^^^

To run a *test* web server on port *port*, you can run this command::

    $ ./src/manage.py runserver <port>

To run a *production* FastCGI server, run this command::

    $ ./src/manage.py runfcgi

Look at the `Django documentation
<https://docs.djangoproject.com/en/1.4/ref/django-admin/#runfcgi-options>`_ for
more information about the options of theses commands.


Test-suite
----------

To run the test-suite you need *python-nose*.

Then, from the root directory of SLAM, you can run this command::

    nosetests

You can also see the test-suite code coverage if you have *nose-cov*
installed::

    nosetests --with-cov --cov-report term-missing --cov src/

Documentation
-------------

To generate the documentation, you need *python-spinx*, then, from the *doc*
directory you can run this command to see all the available output formats::

    make help

And choose the one you prefer::

    make html
