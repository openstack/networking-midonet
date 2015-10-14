=============
Upgrade Notes
=============

This section describes changes which might impact upgrades from the previous
releases.

--------------------
From Kilo to Liberty
--------------------

- A separate plugin ("v2 plugin") which is compatible with MidoNet v2015.09
  was introduced::

      core_plugin = midonet.neutron.plugin_v2.MidonetPluginV2
      service_plugins = midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlug

- Plugin entry point for v1 plugin (the older plugin which is compatible with
  MidoNet v2015.03 and v2015.06) has been moved out of Neutron tree:

  Before::

      core_plugin = neutron.plugins.midonet.plugin.MidonetPluginV2

  After::

      core_plugin = midonet.neutron.plugin_v1.MidonetPluginV2

- `midonet-db-manage` command has been removed.
  You can use `neutron-db-manage --subproject networking-midonet` instead.

  For example,::

      neutron-db-manage --subproject networking-midonet upgrade head
