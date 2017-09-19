..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/


==================
Uplink Network API
==================

MidoNet plugin implements the provider network Neutron extension API, and makes
slight modification to the port binding extension API implementation to
simplify the uplink port configuration of the edge routers.


Problem Description
===================

The edge routers are virtual routers that interface with the uplink routers
outside of the cloud.  Thus, the ports on these virtual routers must be bound
to the interfaces on the edge hosts of the MidoNet deployment.  The MidoNet
Neutron Plugin, however, does not offer any API to create a port on the edge
router.  Furthermore, Neutron requires that all ports are created on a network,
so the concept of having a port directly on a router must be emulated using
the Neutron constructs.


Proposed Change
===============

Because Neutron does not allow creation of a port directly on a router, a
network must be created for any port to exist.  This network must be flagged as
a special network to indicate that it is an 'uplink' network so that MidoNet
would know that the ports on this network need be treated as router ports bound
directly on the physical hosts (as opposed to normal network ports).  Normal
networks cannot be used for this purpose because in the future MidoNet will
support binding of ports on any network, which must be differentiated from
binding ports on the edge router.

To mark these networks as uplink networks, implement the "provider network"
Neutron extension API to map virtual networks to the uplink networks in the
underlay.  Once a virtual network is mapped to a physical network, you
could create a port on this network with binding details to control exactly
which host interface that the port should be bound to.

The 'provider network' extension lets you map a physical network to a virtual
network by associating the virtual network with attributes describing the
physical network.  One of the attributes is called 'network_type' which
could be 'LOCAL', 'FLAT', 'VXLAN', 'VLAN' and 'GRE'.  For the purpose of uplink
network mapping, only the 'LOCAL' network type is accepted by the plugin
because it requires the least amount of extra configurations.  To create an
uplink network, only 'network_type' needs to be specified.

MidoNet currently does not support binding a vlan tagged interface, so the
'VLAN' type cannot be used, but it will be supported in the future.  Likewise,
GRE and VXLAN are not currently supported for binding.

The uplink set up workflow is as follows:

 1. The operator creates a Neutron network mapped to each uplink physical
    network.  The following field should be set for the network to create:

        * "provider:network_type" => Type of the uplink network.  Only 'LOCAL'
                                     type is accepted.

 2. On these networks, create a port for each interface on the host nodes that
    are connected to the uplink networks.  Supply these additional binding
    details for each port created as follows:

        * "binding:host_id" => ID of the host to bind the port on
        * "binding:profile['if_name']" => Name of the interface to bind to

    The host IDs and interface names can be fetched from the 'agents' extension
    API.

 3. For each uplink network port created, execute 'router interface add'
    standard Neutron API to connect the uplink network and the edge router.
    This triggers the binding of the port to the physical interface.  The
    detail of how the binding is achieved is outside of this document's scope.

There are no changes required in the REST API, DB models or client since only
the standard Neutron extension API is invoked.  Please refer to the provider
network extension API document[1] for more details on the workflow.


Database
--------

The only visible change is that the network and port tasks contain new fields:

Network:

::
    "provider:network_type": "LOCAL"

Port:

::
    "binding:host_id": "HOST_ID",
    "binding:profile": {"if_name": "eth0"}


Plugin
------

The 'provider' extension alias is added to the MidoNet plugin.  When looking
up a network, the provider extension attributes must be added to the network
API request and response.

Also, although the plugin already supported 'binding' extension API, the
binding does not include, 'binding:host_id' and 'binding:profile', that are
added to the port API request and response.


Documentation
-------------

The setup of the uplink networks must be described in the Deployment Guide
and/or the Operational Guide.


Alternative Proposal
====================

Instead of using the provider network extension to specify the binding
information for the edge hosts, store the binding information in the MidoNet
agent configuration.  The reason for choosing the proposed approach is that
there was no concrete design agreed by all stakeholders on the agent
configuration approach.


References
==========

[1] http://docs.openstack.org/admin-guide-cloud/content/provider_api_workflow.html
