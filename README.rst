==================
networking-midonet
==================

This is the official Midonet Neutron plugin.


How to Install
--------------

For productional deployments, we recommend to use a package for your
distribution if available::

    http://repo.midonet.org/

You can install the plugin from the source code by running the following
command::

    $ sudo python setup.py install


Core plugin and L3 service plugin
---------------------------------

The following entry in ``neutron.conf`` enables MidoNet as the Neutron plugin.
There are two plugins to choose from.

Plugin v1, which is compatible with MidoNet v2015.03 and v2015.06::

    [DEFAULT]
    core_plugin = midonet.neutron.plugin_v1.MidonetPluginV2

Plugin v2, which is compatible with MidoNet v2015.09 and beyond.
It works with a separate L3 plugin which you need to add to the list of
service plugins::

    [DEFAULT]
    core_plugin = midonet.neutron.plugin_v2.MidonetPluginV2
    service_plugins = midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlugin


LBaaS
-----

Starting in Kilo, MidoNet plugin implements LBaaS v1 following the advanced
service driver model.  To configure MidoNet as the LBaaS driver, set the
following entries in the Neutron configuration file
``/etc/neutron/neutron.conf``::

    [DEFAULT]
    service_plugins = lbaas

    [service_providers]
    service_provider=LOADBALANCER:Midonet:midonet.neutron.services.loadbalancer.driver.MidonetLoadbalancerDriver:default


Tests
-----

You can run the unit tests with the following command::

    $ ./run_tests.sh -f -V

``run_tests.sh`` installs its requirements to ``.venv`` on the initial run.
``-f`` forces a clean re-build of the virtual environment. If you just make
changes on the working tree without any change on the dependencies, you can
ignore ``-f`` switch.

``-V`` or ``--virtual-env`` is specified to use virtualenv and this should be
always turned on.


To know more detail about command options, please execute it with ``--help``::

    $ ./run_tests.sh --help


Creating Packages
-----------------

Run the following command to generate both both the RPM and Debian packages
with the provided version::

    $ ./package.sh some_version


HACKING
-------

To contribute to this repo, please go through the following steps.

1. Keep your working tree updated
2. Make modifications on your working tree
3. Run tests
4. If the tests pass, submit patches to our Gerrit server to get them reviewed
