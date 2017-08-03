========================
DevStack external plugin
========================

networking-midonet has its
`devstack plugin <https://docs.openstack.org/devstack/latest/plugins.html>`_.
The following ``local.conf`` snippet would enable it::

    enable_plugin networking-midonet https://git.openstack.org/openstack/networking-midonet


local.conf examples
-------------------

ML2 Plugin with MidoNet drivers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can find an example at `devstack/ml2/local.conf.sample
<https://git.openstack.org/cgit/openstack/networking-midonet/plain/devstack/ml2/local.conf.sample>`_
in the source tree.

.. literalinclude:: ../../../devstack/ml2/local.conf.sample


MidoNet backend communication
-----------------------------

MidoNet exposes two ways to communicate to its service:

1. REST (synchronous)
2. Tasks DB (asynchronous - experimental)

By default, the plugin is configured to use the REST API service.
The REST API client is specified as::

    MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient

If you want to use the experimental Tasks based API, set the following::

    MIDONET_CLIENT=midonet.neutron.client.cluster.MidonetClusterClient


FWaaS
-----

MidoNet implements Neutron FWaaS extension API.
To configure it with devstack, make sure the following is defined
in ``local.conf``::

    enable_plugin neutron-fwaas https://github.com/openstack/neutron-fwaas
    enable_service q-fwaas
    FWAAS_PLUGIN=midonet_firewall


VPNaaS
------

Starting v5.1, MidoNet implements Neutron VPNaaS extension API.
To configure MidoNet as the VPNaaS driver when running devstack, make sure the
following is defined in ``local.conf``::

    enable_plugin neutron-vpnaas https://github.com/openstack/neutron-vpnaas
    enable_service neutron-vpnaas
    NEUTRON_VPNAAS_SERVICE_PROVIDER="VPN:Midonet:midonet.neutron.services.vpn.service_drivers.midonet_ipsec.MidonetIPsecVPNDriver:default"

NOTE: Currently, this devstack plugin doesn't install ipsec package "libreswan".
Please install it manually.


Gateway Device Management Service
---------------------------------

Starting v5.1, MidoNet implements
Neutron Gateway Device Management Service extension API.
To configure MidoNet including Gateway Device Management Service
when running devstack, make sure the following is defined in ``local.conf``::

    Q_SERVICE_PLUGIN_CLASSES=midonet_gwdevice


L2 Gateway Management Service
---------------------------------

Starting v5.1, MidoNet implements
Neutron L2 Gateway Management Service extension API.
To configure MidoNet including L2 Gateway Management Service
when running devstack, make sure the following is defined in ``local.conf``::

    enable_plugin networking-l2gw https://github.com/openstack/networking-l2gw
    enable_service l2gw-plugin
    Q_PLUGIN_EXTRA_CONF_PATH=/etc/neutron
    Q_PLUGIN_EXTRA_CONF_FILES=(l2gw_plugin.ini)
    L2GW_PLUGIN="midonet_l2gw"
    NETWORKING_L2GW_SERVICE_DRIVER="L2GW:Midonet:midonet.neutron.services.l2gateway.service_drivers.l2gw_midonet.MidonetL2gwDriver:default"


BGP dynamic routing service
---------------------------

Starting v5.2, MidoNet implements Neutron BGP dynamic routing service extension API.
The implementation differs slightly from upstream.
In MidoNet, router treated as bgp-speaker must be specified.

To configure MidoNet including BGP dynamic routing service
when running devstack, make sure the following is defined in ``local.conf``::

    enable_plugin neutron-dynamic-routing https://git.openstack.org/openstack/neutron-dynamic-routing
    DR_MODE=dr_plugin
    BGP_PLUGIN=midonet_bgp
    enable_service q-dr


Logging Resource Service
------------------------

Starting v5.2, MidoNet implements Neutron Logging Resource Service extension API.

To configure MidoNet including Logging Resource Service when running devstack,
make sure the following is defined in ``local.conf``::

    Q_SERVICE_PLUGIN_CLASSES=midonet_logging_resource

QoS
---

The following ``local.conf`` snippet would enable QoS extension with
MidoNet driver::

    enable_plugin neutron https://github.com/openstack/neutron
    enable_service q-qos


LBaaS v2
--------

The following ``local.conf`` snippet would enable LBaaS v2 extension with
MidoNet driver::

    enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas
    enable_service q-lbaasv2
    NEUTRON_LBAAS_SERVICE_PROVIDERV2="LOADBALANCERV2:Midonet:midonet.neutron.services.loadbalancer.v2_driver.MidonetLoadBalancerDriver:default"


Tap as a service
----------------

The following ``local.conf`` snippet would enable Tap-as-a-service support::

    enable_plugin tap-as-a-service https://git.openstack.org/openstack/tap-as-a-service
    enable_service taas
    TAAS_SERVICE_DRIVER="TAAS:Midonet:midonet.neutron.services.taas.service_drivers.taas_midonet.MidonetTaasDriver:default"
