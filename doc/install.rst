Install
=======

This section explain how to properly set-up SLAM to be able to use it.

Install
-------

1. Extract archive or clone the repository
2. Configure and setup the database: you can use one of these methods:

 * Use the quick and easy method: just run::

    $ ./quick_setup.sh

 * Configure SLAM options and create the database:

  * Edit the file **src/configuration.py** and fill at least the :ref:`db-config`
  * run this command to create the database::

    $ python ./src/manage.py syncb

  * then compile the translation files by running theses commands::

    $ cd ./src/webinterface
    $ python ../manage.py compilemessages

3. Use any of the two interface provided (CLI or Web)

.. _db-config:

Database configuration
----------------------

The database can be configured in the file **src/configuration.py**.

Example with sqlite::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/slam.db',
            'USER': '',
            'PASSWORD': '',
            'HOST': '',
            'PORT': '',
        }
    }

Available databases are *sqlite3*, *postgresql_psycopg2*, *mysql*, *oracle* and
more, depending on your Django set-up.

Running the Web server
----------------------

You should refer to this page to choose the last advised method to run a
production Web server for Django:
`<https://docs.djangoproject.com/en/1.4/howto/deployment/>`_.

Test server
^^^^^^^^^^^

A small web server for testing purpose only can be run with this command::

    $ python manage.py runserver <port>

where *port* is the port to listen connection on. For example if you launch the
server with::

    $ python manage.py runserver 8080

You will be able to access the interface at this address:
`<http://127.0.0.1:8080>`_.

Production FastCGI server
^^^^^^^^^^^^^^^^^^^^^^^^^

One solution to launch a production server is to use the Django's FastCGI
server. This allow to use existing HTTP servers already running on a server.
It can be run with::

    $ python manage.py runfcgi host=127.0.0.1 port=8080

This will spawn a FastCGI server that listens on 127.0.0.1:8080.

You will then need to find how to proxify the requests to this FactCGI server
by looking in your HTTP server's documentation.

For *Nginx*, the configuration could be::

    server {
        listen 80 default_server;
        root /srv/www;
        location / {
            fastcgi_pass 127.0.0.1:8080;
        }
    }

Other configuration
-------------------

The *DEBUG* variable should be set to *False* in a production environnment.

You can the name and email address of the administrator of this application in
the *ADMINS* list.

The *TIME_ZONE* and *LANGUAGE_CODE* variables can be changed to the proper
values corresponding to your region.

The *SECRET_KEY* variable must be set to a random and private value. You can
generate a proper one with the following command::

    echo "`</dev/urandom tr -dc '[:graph:]' | head -c50`"
