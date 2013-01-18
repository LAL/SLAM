Technologies
------------

This is a summary of the technologies SLAM uses and what they are used for:

    * SLAM, the actual tool

        * **python** (2.6) as the main programming language
        * **Django** (*python-django*): framework used as Web interface and as
          an ORM for the application
        * **SQLite** as the database backend, can be changed by users by only
          changing one configuration variable

    * SLAM's versioning system

        * **Git**: distributed versioning system

    * SLAM's installation

        * custom **shell** script: automatic configuration of the project
        * **python** script provided by Django: initialize the database, start
          the Web server…

    * SLAM's testing and integration, used for code-style, unit, functional
      testing

        * **pylint**: very customizable coding-style and programming mistakes
          checker
        * **NOSE** (*python-nose*): simple and complete test framework for
          Python applications
        * **NOSE's coverage plugin** (*nose-cov*): used to get a complete and
          precise report on the test-suite code coverage
        * **Jenkins**: continuous integration software that poll the repository
          and automatically launch the full sytle and test-suite each day or
          for any change in the repository

    * SLAM's documentation and project management

        * **SPHINX** (*python-sphinx*): generate the documentation in multiple
          formats (HTML, PDF, epub, texinfo…) from *reStructuredText* files
        * **Trac**: the Wiki and the bug tracker are the main tools we use


Global Architecture
-------------------

Core
^^^^

The core of the project is composed of models: Host, Pool, Address, Property
that are the structures used by Django to represent data in the database; the
address ranges and collections: Ip4Range for IPv4, Ip6Range for IPv6 and
AddressSet for arbitrary addresses; and generators that output configuration
file for a specific software or service.

Most of the core processing happens in the address ranges and in the *Pool*
class. Address ranges store a collection of address and *Pool* keeps track of
the status of the address of one of these collection (allocated or available).

Properties can be added to a *Host* or a *Pool* and can be used to add any
information of type (key: value).

Interfaces
^^^^^^^^^^

Two interfaces are provided by default : CLI and Web with Django. They interact
directly with the SLAM Django application through the **slam.interface**
module. This module provides several helper function to perform various usual
task. New interfaces should use these functions as much as possible but can
very well interact directly with the SLAM Django application.

REST and Web interfaces
"""""""""""""""""""""""

It was chosen to merge these two interfaces because a lot of code would have
been duplicated between these two interfaces if they were split. Furthermore,
thanks to Django's template system and its REST middleware, the distinction is
really no that strong. It also allow to only test the REST interface with the
JSON output and consider the Web interface is tested as well because the
treatments are exactly the same and parsing the JSON output is far easier than
HTML.

For user input, the problem was that HTML does not allow the generation of
query with PUT and DELETE method which are required to provide a sane REST
interface (it was added to the HTML5 specification at some point but has been
removed since). However a really simple Django middleware can be used to
transparently make the conversion between POST request with hidden fields and
HTTP methods which allow us to receive only proper REST query without any
effort.

For output, a simple in-url setting (*format*) allow the user to specify that
he expect a specific output format such as *json*. This is implemented really
easily thanks to Django's template system and the only difference between the
HTML and JSON format is the template used.

Interface Translation
"""""""""""""""""""""

We chose to only translate the Web interface. This is done easily with the
internationalization module of Django which generate automatically *.po* files
for easy translation.

Generators
^^^^^^^^^^

Generators inherit from *Confg* in **slam.generator** and can overwrite
*gen_header*, *gen_footer* and *generate* to customize the behavior of the
generator. For example, the *Bind* generator uses *gen_header* to parse the
*SOA* record and increment it. They can also declare their format of comment
that will be used to generate the SLAM headers in the generated configuration
file.

Tests
^^^^^

Tests are stored in their own files in the **/test** directory, regrouped by
tested python modules. They are executed on an independant database. Tests that
need to compare output use *StringIO* and test that need to provide an input
stream uses a simple pipe.

Evolution
---------

New category model
^^^^^^^^^^^^^^^^^^

A new category model is in progress on the branch *new_category_model*. The
idea is to remove the concept of category and to replace it by *HostType* and
*AddrType*.

The aimed model is that a pool can be linked to several *AddrType* which
defines the way addresses will be generated (it embeds several attributes such
as the way aliases are handled, DNS TTL, DNS zone, etc.). Each *Host* has a
*HostType* which defines its category (pc, laptop, server...). The *HostType*
has a list of *AddrTypes* that will be automatically allocated at the host's
creation and which is represented by a custom relation (*HostTypeAddrType*).
This relation allow to specify that a given *HostType* will have automatically
at its creation.

**HostType**:

    * name,
    * name_format: would be a special formatted string to allow a host name to
      be automatically generated from their IP, category, etc.

**AddrType**:

    * name,
    * dns_zone: the domain of which this host is a sub-domain,
    * dns_alias: describes how the alias are treated when dns records are
      generated. Aliases could be ignore, or generated as CNAME, or as
      alternative A records,
    * dhcp_alias: describes how the alias are treated when dhcp records are
      generated.
    * dns_timeout: the TTL for the generated DNS records.

**HostTypeAddrType**:

    * hosttype,
    * addrtype: *AddrType* to automatically allocate when the host is created,
    * count: number of this *AddrType* to allocate to the host.

Still todo on the new_category_model branch
"""""""""""""""""""""""""""""""""""""""""""

The models are finished, common interface to add and modify HostType and
AddrType is done in slam/interface.py. It needs to be integrated in the CLI
interface and the web interface.

The three interfaces (common, CLI and Web) need to be modified to integrate the
new types, and to allocate automatically addresses related to the types, write
a new interface to list objects from the two new classes, and so on.
Generators also need to be heavily modified to integrate this new model and
generate different things depending on the new attributes.

All the documentation and tests need to be written.

Interface with the DHCP server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The CLI interface has the option **--lastuse**, it can be used to record the
last query seen by the DHCP server for a particular host and address.
An interface could easily made by parsing the DHCP log files to track the
unused addresses.

Improvements to the CLI interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The whole CLI interface is quite terrible, with to much options and a lot of
implicit behaviors. It should be remade from scratch.
