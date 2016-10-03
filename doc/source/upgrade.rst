=============
Upgrade Notes
=============

This section describes changes which might impact upgrades from the previous
releases.

----------------------
From Liberty to Mitaka
----------------------

- Neutron MidoNet interface driver has been moved out of Neutron tree.
  If your deployment uses Neutron DHCP agent and its configuration doesn't
  use the stevedore alias ("midonet"), you should update it:

  Before::

    interface_driver = neutron.agent.linux.interface.MidonetInterfaceDriver

  After::

    interface_driver = midonet

- The following sub-commands were removed from `midonet-db-manage` command::

    current             Display the current revision for a database.
    history             List changeset scripts in chronological order.
    branches            Show current branch points
    check_migration     Show current branch points and validate head file
    upgrade             Upgrade to a later version.
    downgrade           (No longer supported)
    stamp               'stamp' the revision table with the given revision;
    revision            Create a new revision file.

  You can use `neutron-db-manage --subproject networking-midonet` instead.

  For example,::

    $ neutron-db-manage --subproject networking-midonet upgrade head

- At the start of the Mitaka development cycle (immediately after "liberty"
  db milestone), our sub-project db migration chain was separated into
  two branches, "expand" and "contract", to allow a shorter downtime
  as Neutron does.
  See the blueprint [#neutron_online_schema_migrations]_ for details.

.. [#neutron_online_schema_migrations] http://specs.openstack.org/openstack/neutron-specs/specs/liberty/online-schema-migrations.html

--------------------
From Kilo to Liberty
--------------------

- v2 plugin was separated into two plugins, core plugin and L3 service plugin.
  You need to configure L3 service plugin in addition to the core plugin::

    core_plugin = midonet.neutron.plugin_v2.MidonetPluginV2
    service_plugins = midonet.neutron.services.l3.l3_midonet.MidonetL3ServicePlugin

- Plugin entry point for v1 plugin (the older plugin which is compatible with
  MidoNet v2015.03 and v2015.06) has been moved out of Neutron tree:

  Before::

    core_plugin = neutron.plugins.midonet.plugin.MidonetPluginV2

  After::

    core_plugin = midonet.neutron.plugin_v1.MidonetPluginV2

- `midonet-db-manage` command is now obsolete.
  While it's still provided for backward compatibility, we plan to remove
  it in a feature release.
  You can use `neutron-db-manage --subproject networking-midonet` instead.

  For example,::

    $ neutron-db-manage --subproject networking-midonet upgrade head

-----------------
From Juno to Kilo
-----------------

- A separate plugin ("v2 plugin") which is compatible with MidoNet v5.0
  (previously called v2015.09) was introduced::

    core_plugin = midonet.neutron.plugin_v2.MidonetPluginV2
