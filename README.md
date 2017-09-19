# SLAM: Super LAN Address Manager

SLAM (Super LAN Address Manager) is a tool to automatically manage network
addresses allocations. It keeps track of address allocations and can
automatically generate configuration for DNS and DHCP server software and
various other computer and network management software and frameworks like
Quattor.


## Install

*Note: the following instructions assume that you install SLAM in /opt/slam. Update the path
to match your site configuration.*

1. Clone the repository
    ```bash
    cd /opt
    git clone git@github.com:LAL/SLAM.git slam
    # The following command is required for SELinux to work and harmless if not used
    chcon -R -t httpd_sys_content_t /pdisk/slam/src/webinterface/static
    ```
1. Install python-virtualenv and if it is not yet installed
    ```bash
    yum -y install python-virtualenv
    ```
1. Install UWSGI
    ```bash
    yum install uwsgi-plugin-python
    # If using Apache
    yum -y install mod_proxy_uwsgi
    ```
1. Create and activate a Python virtualenv
    ```bash
    virtualenv .venv
    . .venv/bin/activate
    ```
1. Install Python dependencies from PIP (a few RPMs are required for the installation only
   and can be removed after it is complete).
    ```bash
    # Package openldap-devel must be installed before installing python-ldap
    pip install python-ldap
    pip install django_auth_ldap
    # Package mariadb-devel (or mysql-devel depending on what you use) must be installed before installing MySQL-python
    pip install MySQL-python
    # Currently, Django versions > 1.8 don't work with SLAM
    pip install 'Django==1.8'
    ```
1. Initialize the server and its database (first time only)
    ```bash
    ./quick_setup.sh
    python src/manage.py createsuperuser
    python src/manage.py runserver
    ```


## SLAM CLI Usage

*Note: if you are using the recommended virtualenv-based configuration, you must activate the virtual environment before running `slam-cli`. This is
typically done with:*

```bash
. /opt/slam/venv/bin/activate
```

SLAM CLI is `src/slam_cli.py`. Available options are:

```bash
[root@oneprivvm-254 slam]# src/slam_cli.py --help
usage: slam_cli.py [-h] -a
                   {list,create,get,delete,modify,setprop,rmprop,createconf,upconf,log,export}
                   [-pn POOL_NAME] [-c CATEGORY] [-p POOL] [-A ADDRESS]
                   [-m MAC] [-H HOST] [-r] [-g GENERATOR] [-o OUTPUT]
                   [--default] [--header HEADER] [--footer FOOTER]
                   [--checkfile CHECKFILE] [--timeout TIMEOUT]
                   [--domain DOMAIN] [--alias ALIAS] [--inventory INVENTORY]
                   [--serial SERIAL] [--duration DURATION] [--lastuse LASTUSE]
                   [--comment COMMENT] [--nodns]
                   [ARG [ARG ...]]

SLAM command-line interface

positional arguments:
  ARG                   Extra arguments required by specific actions (ie:
                        modify).

optional arguments:
  -h, --help            show this help message and exit
  -a {list,create,get,delete,modify,setprop,rmprop,createconf,upconf,log,export}, --action {list,create,get,delete,modify,setprop,rmprop,createconf,upconf,log,export}
                        The action to perform: list | create | get | delete |
                        modify | setprop | rmprop | createconf | upconf |
                        export
  -pn POOL_NAME, --pool-name POOL_NAME
                        The name of an address pool.
  -c CATEGORY, --category CATEGORY
                        The category of an address pool.
  -p POOL, --pool POOL  Address definition of the pool to manage (ex:
                        10.1.2.0/24, fc00::/7, "addr1,addr2,addr3").
  -A ADDRESS, --address ADDRESS
                        An address to list, allocate or free.
  -m MAC, --mac MAC     A mac-address to bind to a host.
  -H HOST, --host HOST  The name of the host to manage.
  -r, --random          Hosts will get random addresses from the pool.
  -g GENERATOR, --generator GENERATOR
                        Name of the configuration generator.
  -o OUTPUT, --output OUTPUT
                        Output file path for the configuration files to
                        generate, or - for stdout.
  --default             Set the generator as default or toogle its state.
  --header HEADER       Header file path for the configuration files to
                        generate.
  --footer FOOTER       Footer file path for the configuration files to
                        generate.
  --checkfile CHECKFILE
                        Files to scan for duplicates while generating
                        configuration.
  --timeout TIMEOUT     Timeout for the generated configuration (ie: bind...).
  --domain DOMAIN       Domain for the hosts to generate.
  --alias ALIAS         An alias for a host name
  --inventory INVENTORY
                        Inventory number for a host
  --serial SERIAL       Serial number of a machine.
  --duration DURATION   Number of day for a temporary allocation.
  --lastuse LASTUSE     UNIX timestamp of the last use of the address.
  --comment COMMENT     Store a comment related to an address.
  --nodns               No DNS record will be generated for the addresses of
                        this host.
```

Examples:

* Create a new pool

    ```bash
    $ ./src/slam_cli.py
        --action create
        --pool-name localnet
        --pool 10.242.0.0/16
        --category desktop
    ```

* Create a two new hosts and assign them available addresses from the pool:

    ```bash
    $ ./src/slam_cli.py
        --action create
        --host pc42
        --host pc1337
        --pool-name localnet
        --mac 00:11:22:33:44:55
    ```

* Generate the configuration for the Bind DNS server zone file:

    ```bash
    $ ./src/slam_cli.py
        --action createconf
        --output out.zonefile
        bind
    ```


## Web interface Configuration

The SLAM web application is run with UWSGI. UWSGI can be used with Apache or Nginx, according to your preference.

### Apache Configuration

You need to have `mod_proxy_uwsgi` package installed and configured to be one of the loaded module in the server. 
Apache virtual host configuration used for SLAM must typically contain the following lines (in addition to the usual ones):

```
Alias "/static" "/opt/slam/src/webinterface/static"

SetEnv UWSGI_SCHEME https
# First ProxyPass should not be needed but Alais is ignored if not specified (/static passed to uwsgi)
ProxyPass /static !
ProxyPass / uwsgi://127.0.0.1:8008/

<Directory /opt/slam/src/webinterface/static>
    AllowOverride None
    Require all granted
</Directory>
``` 

### UWSGI

To declare SLAM application to UWSGI, you need to create a file `/etc/uwsgi.d/slam.ini` owned by `uwsgi:uwsgi` with the following
contents (adjust paths to your configuration and ensure that directory used for logs, pid and sock exist and are 
writable by `uwsgi` user):

```
[uwsgi]
plugin = python
single-interpreter = true

master=True
pidfile=/tmp/project-master.pid
vacuum=True
max-requests=5000
daemonize=/var/log/uwsgi/slam.log

# chdir is required by Django to be the root of the project files
chdir=/opt/slam/src
touch-reload = /opt/slam/src/webinterface/wsgi.py
wsgi-file = /opt/slam/src/webinterface/wsgi.py
virtualenv = /opt/slam/.venv

socket = 127.0.0.1:8008
stats = /var/run/uwsgi/uwsgi-stats.sock
protocol = uwsgi
```

### SLAM Configuration

SLAM configuration is defined in `configure.py`. This file must be placed either in
a `conf` directory at the same level as `src` directory or in `/etc/slam`. A template 
exists in `conf` directory.

Configuring services like DNS and DHCP with information from SLAM DB requires a script
typically placed in `scripts` directory (at the same level as `src` directory). The LAL
script provided in the repository can be used as a template. The name of the script must be
specified as the value of `RELOAD_SCRIPT` in `configure.py`.

Additionally, if you reuse the LAL deployment script, it requires a `run` directory at the same level as
the `scripts` directory. This directory must be owned by writable by the USWGI account used
to run SLAM (typically `uwsgi`).

### Utilisation

Connect with https to the machine hosting SLAM.

### Troubleshooting

Apart from the Apache logs, the most useful log file is the UWSGI SLAM log file,
`slam.log` under the directory specified by UWSGI configuration option `daemonize`.
You should also check the status reported by the UWSGI service, in particular the
existence of the `slam.ini` child, with:

```bash
systemctl status uwsgi
```

To start a *test* web server on a given _port_ run:
    $ ./src/manage.py runserver <port>

To start a *production* FastCGI server run:
    $ ./src/manage.py runfcgi <option>


## Full documentation

The full documentation is available in sphinx format in the doc/ directory. To
generate it, type :

    make help

Example:
    make html
    make latexpdf


## Test suite

To run the test suite, you need the nose software (*python-nose*).
Then you can run the suite with the following command:

    nosetests
