===========================
networking-midonet devstack
===========================

This is the official Midonet Neutron devstack plugin.


MidoNet Data Service
--------------------

To use the new MidoNet Cluster service:

::

 USE_CLUSTER=True

The default is False, which enables the legacy REST API service.


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
devstack, set the following in local.conf:

::

    enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas
    NEUTRON_LBAAS_SERVICE_PROVIDERV1="LOADBALANCER:Midonet:midonet.neutron.services.loadbalancer.driver.MidonetLoadbalancerDriver:default"
