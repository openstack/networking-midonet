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
2. Copy the sample local.conf.sample_net_only file over to the devstack
directory as local.conf.
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


MidoNet Data Service
--------------------

To use the new MidoNet Cluster service:

::

 USE_CLUSTER=True

The default is False, which enables the legacy REST API service.

Since the cluster service is still in an experimental stage, the 'uplink'
configuration performed at the end of devstack would fail.  To bypass this
error, set the following:

::

 MIDONET_CREATE_FAKE_UPLINK=False


MidoNet Client
--------------

Kilo is compatible with both REST API and Cluster services.  To choose one, set
the MIDONET_CLIENT environment variable appropriately.

The default is the REST API client:

::

 MIDONET_CLIENT=midonet.neutron.client.api.MidonetApiClient


To set the Cluster-based client:

::

 MIDONET_CLIENT=midonet.neutron.client.cluster.MidonetClusterClient


LBaaS
-----

Starting in Kilo, MidoNet plugin implements LBaaS v1 following the advanced
service driver model.  To configure MidoNet as the LBaaS driver when running
devstack, make sure the following is defined in local.conf:

::

    enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas
    NEUTRON_LBAAS_SERVICE_PROVIDERV1="LOADBALANCER:Midonet:midonet.neutron.services.loadbalancer.driver.MidonetLoadbalancerDriver:default"
