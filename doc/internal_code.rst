Internal structures
-------------------

This page describe the internal structures of SLAM.

Models
^^^^^^

Models are used to store information persistently in the database.

Pool class
""""""""""

.. autoclass:: slam.models.Pool

Note: the reason why we use *random.randint* instead of *random.choice* is
because *random.choice* uses *len(range)*, see :ref:`range-len`.

Host class
""""""""""

.. autoclass:: slam.models.Host

Alias Class
"""""""""""

.. autoclass:: slam.models.Alias

Note: relation between Alias and Host is n,m because we want, by design, that
several hosts have the same alias and also that several aliases point to the
same host.

Address class
"""""""""""""

.. autoclass:: slam.models.Address

Property class
""""""""""""""

.. autoclass:: slam.models.Property

Adress collections
^^^^^^^^^^^^^^^^^^

These class represent a collection of address: it can be either an entire
subnet or set of manually defined addresses.

.. _range-len:

addrrange module
""""""""""""""""

Note: we expect these classes to provide a *.len()* method instead of a
*__len__()* because *__len__* expect an integer in python2 which triggers an
exception when we call *len* on an *Ip6Range* which often return a long.

.. automodule:: slam.addrrange

Configuration Generators
^^^^^^^^^^^^^^^^^^^^^^^^

These class are used to generate configuration files for common network
services such as DNS, DHCP or Quattor.

generator module
""""""""""""""""

.. automodule:: slam.generator

Interfaces
^^^^^^^^^^

Generic Interface
"""""""""""""""""

.. automodule:: slam.interface

slam_cli module
"""""""""""""""

.. automodule:: slam_cli

Web Interface
"""""""""""""

.. automodule:: webinterface.views

Tests
^^^^^

Note that a few functionality are not very well tested because they are just a
straight adaptation of the Python built-in structures such as the *AddressSet*
wich is juste a wrapper around python's set.

test_range module
"""""""""""""""""

.. automodule:: test_range

test_pool module
""""""""""""""""

.. automodule:: test_pool

test_cli module
"""""""""""""""

.. automodule:: test_cli
