==============================
Installation and configuration
==============================

Supported MidoNet versions
--------------------------

The current set of supported versions of MidoNet are:

- v5.x

NOTE: MidoNet changed its versioning scheme.
v5.0 is what used to be called v2015.09.

How to Install
--------------

For productional deployments, we recommend to use a package for your
distribution if available:

http://builds.midonet.org/

You can install the plugin from the source code by running the following
command::

    $ sudo python setup.py install

The plugin requires python-midonetclient package, which is usually available
along with other midonet packages.  It's recommended to use the same version
of python-midonetclient and midonet-cluster.  Alternatively, you can install
python-midonetclient from source::

    $ sudo pip install -e 'git://github.com/midonet/midonet.git@master#egg=midonetclient&subdirectory=python-midonetclient'


MidoNet API configuration
-------------------------

You need to configure the Neutron server how to talk with
your MidoNet cluster.

* Prepare a Keystone credential, with which the Neutron server
  will send requests to the MidoNet cluster.

* Configure Keystone authentication in MidoNet.
  See `Using the Keystone authentication service <https://docs.midonet.org/docs/latest-en/operations-guide/content/keystone_authentication.html>`_ in
  MidoNet documentation for details.

* Configure the following options in the Neutron server configuration file.

  :oslo.config:option:`midonet.midonet_uri`
  :oslo.config:option:`midonet.username`
  :oslo.config:option:`midonet.password`
  :oslo.config:option:`midonet.project_id`


ML2 mechanism and type drivers
------------------------------

networking-midonet is compatible with ML2 plugin.
ML2 mechanism driver and type drivers for MidoNet are available::

    [DEFAULT]
    core_plugin = ml2

    [ml2]
    tenant_network_types = midonet
    type_drivers = midonet,uplink
    mechanism_drivers = midonet


L3 service plugin
-----------------

networking-midonet uses its own L3 service plugin::

    [DEFAULT]
    service_plugins = midonet_l3

L3 extensions
~~~~~~~~~~~~~

In addition to the standard ones, networking-midonet L3 service plugin
provides the following extensions.  No additional configurations are
necessary to enable them.  They are enabled unconditionally.

- router-interface-fip (MidoNet 5.1.1 and later)
- fip64 (MidoNet 5.4 and later)


Interaction with Neutron agents
-------------------------------

No Neutron agents are necessary for networking-midonet.

You can configure networking-midonet work with Neutron DHCP and
Metadata agents.  But it isn't recommended anymore.

For details, please refer to MidoNet documentation:

https://docs.midonet.org


.. _interface-driver:

Interface driver
~~~~~~~~~~~~~~~~

Neutron agents use `interface driver` to connect themselves into the datapath.
In case of MidoNet, they should be configured with the MidoNet interface
driver.::

    [DEFAULT]
    interface_driver = midonet


FWaaS
-----

Starting v5.0, MidoNet implements Neutron FWaaS extension API.

To configure it, add the following service plugin to the `service_plugins` list
in the DEFAULT group of ``/etc/neutron/neutron.conf``::

    [DEFAULT]
    service_plugins = midonet_firewall

NOTE: No need to configure `Firewall Driver` at all.  It's irrelevant
because this plugin does not use Neutron L3 agent.


LBaaS v2
--------

Starting v5.4, MidoNet implements Neutron LBaaS v2 extension API.

MidoNet plugin provides LBaaS v2 service driver.

To configure it, add the following entries in the Neutron configuration
file ``/etc/neutron/neutron.conf``::

    [DEFAULT]
    service_plugins = lbaasv2

    [service_providers]
    service_provider=LOADBALANCERV2:Midonet:midonet.neutron.services.loadbalancer.v2_driver.MidonetLoadBalancerDriver:default


VPNaaS
------

Starting v5.1, MidoNet implements Neutron VPNaaS extension API.

MidoNet plugin implements VPNaaS as a service driver.  To configure it,
add the following entries in the Neutron configuration file
``/etc/neutron/neutron.conf``::

    [DEFAULT]
    service_plugins = vpnaas

    [service_providers]
    service_provider=VPN:Midonet:midonet.neutron.services.vpn.service_drivers.midonet_ipsec.MidonetIPsecVPNDriver:default

NOTE: This plugin does not use Neutron VPNaaS agent.


Gateway Device Service
----------------------

Starting v5.1, MidoNet implements Gateway Device Service vendor extension API.

To configure it, add the following service plugin to the `service_plugins` list
in the DEFAULT group of `/etc/neutron/neutron.conf`::

    [DEFAULT]
    service_plugins = midonet_gwdevice


L2 Gateway Service
------------------

Starting v5.1, MidoNet implements Neutron L2 Gateway Service extension API.
The implementation differs slightly from upstream.
Please check the spec to see the differences:

https://docs.openstack.org/networking-midonet/latest/specs/mitaka/border_gw.html

MidoNet plugin implements L2 Gateway Service as a service driver.
To configure it, add the following service plugin to the `service_plugins` list
in the DEFAULT group of `/etc/neutron/neutron.conf`::

    [DEFAULT]
    service_plugins = midonet_l2gw

In addition, configure the service provider in the 'service_providers' group of
L2 Gateway plugin configuration file `/etc/neutron/l2gw_plugin.ini`::

    [service_providers]
    service_provider = L2GW:Midonet:midonet.neutron.services.l2gateway.service_drivers.l2gw_midonet.MidonetL2gwDriver:default


BGP dynamic routing service
---------------------------

Starting v5.2, MidoNet implements Neutron BGP dynamic routing service extension API.
The implementation differs from upstream as follows:

- Router that is treated as bgp-speaker can be specified explicitly.
- Bgp-peer can relate to only one bgp-speaker.
- Binding network to bgp-speaker must be done before associating peers.
- Removing network from bgp-speaker must be done after all peers are
  disassociated from the bgp-speaker.
- Only one network can be associated with a bgp-speaker.
- Advertise_floating_ip_host_routes and advertise_tenant_networks are ignored.
- Attached network to the router and destination network in extra routes on the
  router are showed as advertised routes.

To configure it, add the following service plugin to the `service_plugins` list
in the DEFAULT group of `/etc/neutron/neutron.conf`::

    [DEFAULT]
    service_plugins = midonet_bgp


Logging Resource Service
------------------------

Starting v5.2, MidoNet implements Neutron Logging Resource Service extension API.

To configure it, add the following service plugin to the `service_plugins` list
in the DEFAULT group of `/etc/neutron/neutron.conf`::

    [DEFAULT]
    service_plugins = midonet_logging_resource

Firewall log is managed by Quota.
Default value of firewall log is 10 that is same number as firewall.
Basically, both Quota value for firewall and firewall log should be aligned.
To tune it, change value of `quota_firewall_log` in the quotas group of
`/etc/neutron/neutron.conf`.


Tap-as-a-Service
----------------

Starting v5.2, MidoNet implements Tap-as-a-Service extension API.

MidoNet plugin implements TaaS as a service driver.  To configure it,
add the following entries in the Neutron configuration file
`/etc/neutron/neutron.conf`::

    [DEFAULT]
    service_plugins = taas

In addition, configure the service provider in the 'service_providers' group of
TaaS plugin configuration file `/etc/neutron/taas_plugin.ini`::

    [service_providers]
    service_provider = TAAS:Midonet:midonet.neutron.services.taas.service_drivers.taas_midonet.MidonetTaasDriver:default


QoS
---

Starting v5.4, MidoNet implements Neutron QoS extension API.
It's automatically enabled when QoS service plugin is configured.
No MidoNet-specific configuration is necessary.

QoS service plugin
~~~~~~~~~~~~~~~~~~

QoS service plugin can be configured in the Neutron server configuration
file `/etc/neutron/neutron.conf`::

    [DEFAULT]
    service_plugins = qos

QoS core resource extension for ML2
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

QoS core resource extension for ML2 plugin can be configured in the
Neutron server configuration file `/etc/neutron/neutron.conf`::

    [ml2]
    extension_drivers = qos


Horizon
-------

Starting with Newton, Horizon has built-in support for MidoNet network types.

To enable it, add the following configuration to the
`OPENSTACK_NEUTRON_NETWORK` dict in `local_settings.py`::

    'supported_provider_types': ['midonet', 'uplink'],


Magnum
------

Starting v5.2, MidoNet can be used for Magnum deployment.
