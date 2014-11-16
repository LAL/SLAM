SLAM: Super LAN Address Manager
===============================

SLAM (Super LAN Address Manager) is a tool to automatically manage network
addresses allocations. It keeps track of address allocations and can
automatically generate configuration for DNS and DHCP server software and
various other computer and network management software and frameworks like
Quattor.


Install
-------

 1. Extract archive or clone the repository
 2. Configure and setup the database, you can use one of these methods :
    * Use the quick and easy method: juste run
        $ ./quick_setup.sh
    * Configure SLAM options and create the database:
        * Edit *src/configuration.py* and fill at least the database section
        * Run this command to create the database:
            $ python ./src/manage.py syncdb
        * Run these commands to compile translation files:
            $ cd ./src/webinterface
            $ python ../manage.py compilemessages
 3. Use any of the two avaible interfaces: CLI or Web.


Usage
-----

    ./slam_cli.py
        [-h]
        -a {list|create|get|delete|modify|setprop|rmprop|createconf|upconf|log|export}
        [-pn POOL_NAME]
        [-p POOL]
        [-A ADDRESS]
        [-H HOST]
        [-m MAC]
        [--alias ALIAS]
        [-c CAT]
        [-r]
        [-g GEN]
        [--default]
        [--header HDR]
        [--footer FTR]
        [-o OUTFILE]
        [--checkfile CHECK]
        [--serial SERIAL]
        [--inventory INVENTORY]
        [--duration DAYS]
        [--lastuse LAST]
        [ARG...]

arguments:
```
    -h, --help            show this help message and exit
    -a, --action {list,create,delete,modify,createconf,upconf|log|export}
                          The action to perform: list | create | delete
                          | modify |setprop | rmprop | createconf | upconf
                          | log | export
    -pn, --pool-name POOL_NAME
                          The name of an address pool.
    -p, --pool POOL       Address definition of the pool to manage (ex:
                          10.1.2.0/24, fc00::/7, "addr1,addr2,addr3").
    -A, --address ADDRESS An address to list, allocate or free.
    -H, --host HOST       The name of the host to manage.
    -m, --mac MAC         The mac address to assign to a host.
    --alias ALIAS         One or more alias for the host name.
    -c, --category CAT    The category of pool to create or assign host to.
    -r, --random          Hosts will get random addresses from the pool.
    -g, --generator GEN   The name of the generator to retrieve from database
                          to create.
    --default             Set the generator as default for the given
                          configuration type or toggle it.
    --header HDR          The file to insert before the content when generating
                          configuration files.
    --footer FTR          The file to insert after the content when generating
                          configuration files.
    --output OUTFILE      The file to write the configuration to or - to output
                          on the stdout.
    --serial SERIAL       Specify the serial number of a host.
    --inventory INVENTORY Specify the inventory number of a host.
    --comment COMMENT     Add a comment to this address.
    --duration DAYS       Allocate the new address for a temporary duration of
                          DAYS of days.
    --lastuse LAST        Specify that this host and address has been seen on
                          the network for the last time at timestamp LAST.
    ARG...                Extra arguments required by specific actions
                          (ie: modify, setprop)
```

Example:

    Create a new pool
    $ ./src/slam_cli.py
        --action create
        --pool-name localnet
        --pool 10.242.0.0/16
        --category desktop

    Create a two new hosts and assign them available addresses from the pool:
    $ ./src/slam_cli.py
        --action create
        --host pc42
        --host pc1337
        --pool-name localnet
        --mac 00:11:22:33:44:55

    Generate the configuration for the Bind DNS server zone file:
    $ ./src/slam_cli.py
        --action createconf
        --output out.zonefile
        bind


Web interface usage
-------------------

To start a *test* web server on a given _port_ run:
    $ ./src/manage.py runserver <port>

To start a *production* FastCGI server run:
    $ ./src/manage.py runfcgi <option>


Full documentation
------------------

The full documentation is available in sphinx format in the doc/ directory. To
generate it, type :

    make help

Example:
    make html
    make latexpdf


Test suite
----------

To run the test suite, you need the nose software (*python-nose*).
Then you can run the suite with the following command:

    nosetests
