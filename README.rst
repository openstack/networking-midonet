==================
networking-midonet
==================

This is the official Midonet Neutron plugin.

The current set of supported versions of MidoNet are:

- v2015.03
- v2015.06
- v5.0

NOTE: MidoNet recently changed its versioning scheme.
v5.0 is what used to be called v2015.09.


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

Plugin v2, which is compatible with MidoNet v5.0 and beyond.
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


HACKING
-------

To contribute to this repo, please go through the following steps.

1. Keep your working tree updated
2. Make modifications on your working tree
3. Run tests
4. If the tests pass, submit patches to our Gerrit server to get them reviewed
