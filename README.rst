==================
networking-midonet
==================

This is the official Midonet Neutron plugin.


How to Install
--------------

Run the following command to install the plugin in the system:

::

    $ sudo python setup.py install


The following entry in ``neutron.conf`` enables MidoNet as the Neutron plugin:

::
    core_plugin = neutron.plugins.midonet.plugin.MidonetPluginV2


The Kilo MidoNet plugin is not compatible with MidoNet prior to 2.0.  Please
use the Juno plugin if you want to use it against MidoNet version 1.X.


Configure
---------

Configuring the Midonet Plugin is done by modifying the midonet.ini file
found by default at

::

    /etc/neutron/plugins/midonet.ini


In order to enable more extensions, add the extension names in a list to
the 'extra_extensions' key under the MIDONET section:

::

    extra_extensions = agent-membership,extraroute


LBaaS
-----

Starting in Kilo, MidoNet plugin implements LBaaS v1 following the advanced
service driver model.  To configure MidoNet as the LBaaS driver, set the
following entries in the Neutron configuration file
(/etc/neutron/neutron.conf):

::
    [DEFAULT]
    service_plugins = lbaas

    [service_providers]
    service_provider=LOADBALANCER:Midonet:midonet.neutron.services.loadbalancer.driver.MidonetLoadbalancerDriver:default


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

Run the following command to generate both both the RPM and Debian packages
with the provided version:
::

    $ ./package.sh some_version


HACKING
-------

To contribute to this repo, please go through the following steps.

1. Keep your working tree updated
2. Make modifications on your working tree
3. Run tests
4. If the tests pass, submit patches to our Gerrit server to get them reviewed
