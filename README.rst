python-neutron-plugin-midonet
=============================

This is the downstream Midonet Neutron plugin.


How to Install
--------------

Run the following command to install the plugin in the system.

    $ sudo python ./setup.py


In ``neutron.conf``, set the core_plugin to:

::

    core_plugin = midonet.neutron.plugin.MidonetPluginV2


Tests
-----

You can run the unit tests with the following command.::

    $ ./run_tests.sh -f -V

``run_tests.sh`` installs its requirements to ``.venv`` on the initial run.
``-f`` forces a clean re-build of the virtual environment. If you just make
changes on the working tree without any change on the dependencies, you can
ignore ``-f`` switch.

``-V`` or ``--virtual-env`` is specified to use virtualenv and this should be
always turned on.


To know more detail about command options, please execute it with ``---help``.::

    $ ./run_tests.sh --help


Creating Packages
-----------------

    $ ./package.sh v1.0
    
``package.sh`` generates both the RPM and Debian packages with the provided version.


HACKING
-------

To contribute to this repo, please go through the following steps.

1. Keep your working tree updated
2. Make modifications on your working tree
3. Run tests
4. If the tests pass, submit patches to our Gerrit server to get them reviewed
