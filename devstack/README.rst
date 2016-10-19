========================
DevStack external plugin
========================


To Run DevStack with Full OpenStack Environment
-----------------------------------------------

1. Download DevStack
2. Prepare ``local.conf``
3. Run ``stack.sh``

There are more detailed info on the wiki.
https://github.com/midonet/midonet/wiki/Devstack


To Run DevStack with monolithic midonet plugin
-----------------------------------------------

1. Download DevStack
2. Copy the sample ``midonet/local.conf.sample`` file over to the devstack
   directory as ``local.conf``.
3. Run ``stack.sh``


To Run DevStack with ML2 and midonet mechanism driver
-----------------------------------------------------

1. Download DevStack
2. Copy the sample ``ml2/local.conf.sample`` file over to the devstack directory
   as ``local.conf``.
3. Run ``stack.sh``

Note that with these configurations, only the following services are started::

    rabbit
    mysql
    keystone
    nova
    glance
    neutron
    lbaas
    tempest
    horizon


Plugin
------

There are two versions of MidoNet plugin.  Set MIDONET_PLUGIN local.conf
variable to the plugin that you want to load.

MidoNet plugin v1, which is compatible with MidoNet v2015.06::

    MIDONET_PLUGIN=midonet

MidoNet plugin v2, which is compatible with MidoNet v5.0 and beyond::

    MIDONET_PLUGIN=midonet_v2


MidoNet Data Service
--------------------

On the master branch of MidoNet, there are two types of Zookeeper data store
engines available:

1. DataClient (legacy)
2. ZOOM (default)

By default, the ZOOM backend is enabled.  If you want to use the legacy
DataClient data store, set the following::

    MIDONET_USE_ZOOM=False

Also, MidoNet exposes two ways to communicate to its service:

1. REST (synchronous)
2. Tasks DB (asynchronous - experimental)

By default, the plugin is configured to use the REST API service.  The REST API
client is specified as::

    MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient

If you want to use the experimental Tasks based API, set the following::

    MIDONET_CLIENT=midonet.neutron.client.cluster.MidonetClusterClient

There are three ways in which the Neutron plugin could access MidoNet:

1. MidoNet REST API with DataClient (legacy version)::

    MIDONET_PLUGIN=midonet
    MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient
    MIDONET_USE_ZOOM=False

2. MidoNet REST API with ZOOM (current version)::

    MIDONET_PLUGIN=midonet_v2
    MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient
    MIDONET_USE_ZOOM=True

3. MidoNet Tasks API with ZOOM (experimental version)::

    MIDONET_PLUGIN=midonet_v2
    MIDONET_CLIENT=midonet.neutron.client.cluster.MidonetClusterClient
    MIDONET_USE_ZOOM=True


FWaaS
-----

Starting v5.0, MidoNet implements Neutron FWaaS extension API.
To configure it with devstack, make sure the following is defined
in ``local.conf``::

    enable_plugin neutron-fwaas https://github.com/openstack/neutron-fwaas
    enable_service q-fwaas
    FWAAS_PLUGIN=midonet_firewall


LBaaS
-----

MidoNet plugin implements LBaaS v1 following the advanced service driver model.
To configure MidoNet as the LBaaS driver when running devstack, make sure the
following is defined in ``local.conf`` together with enabling q-lbaasv1 service::

    enable_plugin neutron-lbaas https://github.com/openstack/neutron-lbaas
    NEUTRON_LBAAS_SERVICE_PROVIDERV1="LOADBALANCER:Midonet:midonet.neutron.services.loadbalancer.driver.MidonetLoadbalancerDriver:default"


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

    Q_SERVICE_PLUGIN_CLASSES=midonet_bgp


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

    [[post-config|$NEUTRON_CONF]]
    [qos]
    notification_drivers = midonet

Note: Make sure you're using ML2 plugin.  MidoNet monolithic plugins
(either v1 or v2) do not support QoS core resource extension.
