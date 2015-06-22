===========================
networking-midonet devstack
===========================

This is the official Midonet Neutron devstack plugin.

To Run DevStack with Full OpenStack Environment
-----------------------------------------------

1. Download DevStack
2. Prepare local.conf
3. Run ``stack.sh``

There are more detailed info on the wiki.
http://wiki.midonet.org/Devstack


To Run DevStack with Networking-Only Environment
------------------------------------------------

1. Download DevStack
2. Copy the sample local.conf.sample file over to the devstack directory as
local.conf.
3. Run ``stack.sh``

Note that with these configurations, only the following services are started::

    rabbit
    mysql
    keystone
    nova
    glance
    neutron (with DHCP and metadata agents)
    lbaas
    tempest
    horizon


Kilo Plugin
-----------

There are two versions of Kilo plugin.  Set MIDONET_PLUGIN local.conf
variable to the Kilo plugin that you want to load.

Kilo plugin v1, which is compatible with MidoNet v2015.03 and v2015.06:

::
    MIDONET_PLUGIN=neutron.plugins.midonet.plugin.MidonetPluginV2


Kilo plugin v2, which is compatible with MidoNet v2015.09 and beyond:

::
    MIDONET_PLUGIN=midonet.neutron.plugin_v2.MidonetPluginV2


MidoNet Data Service
--------------------

On the master branch of MidoNet, there are two types of Zookeeper data store
engines available:

 1. DataClient (legacy)
 2. ZOOM (enhanced version still in an experimental stage)

Also, MidoNet exposes two API services:

 1. MidoNet API (legacy REST)
 2. Cluster API/RPC (new API providing both REST and protobuf-based RPC)

By default, when running devstack, both MidoNet API and MidoNet Cluster
services are spawned.  Kilo is compatible with both the API and the Cluster,
and to toggle between the two, configure the MIDONET_CLIENT envrionment
variable appropriately.

In addition, the MidoNet agent must be instructed to use either DataClient
(default) or ZOOM.

There are three ways in which the Neutron plugin could access MidoNet:

1. MidoNet API with DataClient (legacy version)::

 MIDONET_PLUGIN=neutron.plugins.midonet.plugin.MidonetPluginV2
 MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient
 MIDONET_USE_ZOOM=False

2. MidoNet API with ZOOM (transitional version)::

 MIDONET_PLUGIN=midonet.neutron.plugin_v2.MidonetPluginV2
 MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient
 MIDONET_USE_ZOOM=True

3. MidoNet Cluster with ZOOM (final version)::

 MIDONET_PLUGIN=midonet.neutron.plugin_v2.MidonetPluginV2
 MIDONET_CLIENT=midonet.neutron.client.cluster.MidonetClusterClient
 MIDONET_USE_ZOOM=True

Finally, since the cluster service is still in an experimental stage, the
'uplink' configuration performed at the end of devstack would fail.  To bypass
this error, set the following:

::

 MIDONET_CREATE_FAKE_UPLINK=False


LBaaS
-----

Starting in Kilo, MidoNet plugin implements LBaaS v1 following the advanced
service driver model.  To configure MidoNet as the LBaaS driver when running
devstack, make sure the following is defined in local.conf:

::

    enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas
    NEUTRON_LBAAS_SERVICE_PROVIDERV1="LOADBALANCER:Midonet:midonet.neutron.services.loadbalancer.driver.MidonetLoadbalancerDriver:default"
