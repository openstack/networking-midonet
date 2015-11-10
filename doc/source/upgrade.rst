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

      interface_driver = neutron.agent.linux.interface:MidonetInterfaceDriver

  After::

      interface_driver = midonet

--------------------
From Kilo to Liberty
--------------------

- A separate plugin ("v2 plugin") which is compatible with MidoNet v5.0
  (previously called v2015.09) was introduced::

      core_plugin = midonet_v2
      service_plugins = midonet_l3

- Plugin entry point for v1 plugin (the older plugin which is compatible with
  MidoNet v2015.03 and v2015.06) has been moved out of Neutron tree:

  Before::

      core_plugin = midonet

  After::

      core_plugin = midonet_v2

- `midonet-db-manage` command is now obsolete.
  While it's still provided for backward compatibility, we plan to remove
  it in a feature release.
  You can use `neutron-db-manage --subproject networking-midonet` instead.

  For example,::

      neutron-db-manage --subproject networking-midonet upgrade head
