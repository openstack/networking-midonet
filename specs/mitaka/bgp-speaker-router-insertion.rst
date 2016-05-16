..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

======================================
BGP Speaker Insertion Model on Routers
======================================

This spec describes an extension to associate a BGP speaker to a router.

For detailed explanations of the BGP implementation of networking-midonet,
refer to the BGP Operational Guide [1].


Problem Description
===================

MidoNet BGP model does not match the 'bgp' extension model of Neutron in some
critical ways.  Namely, in MidoNet, BGP must be configured on a router whereas
in Neutron, BGP is configured independently.  There is no way to associate a
BGP speaker to a router in the Neutron's 'bgp' extension model.


Proposed Change
===============

In order to have MidoNet implement 'bgp' extension API of Neutron,
'bgp-speaker-router-insertion' vendor extension API is defined to track the
associations between BGP speakers and routers.

For each BGP speaker, exactly one router is associated.  The IP address used
by the BGP speaker is the IP address on the router port that is on the same
subnet as the BGP peer IP.

With this mode, the following operations no longer become applicable:

 *  add_gateway_network
 *  delete_gateway_network

Invoking these operations on a BGP speaker that has a router associated results
in an error.

Also, the following fields no longer become applicable:

 * advertise_floating_ip_host_routes
 * advertise_tenant_networks

The values set in these fields are ignored.

Since 'bgp-speaker-router-insertion' is a vendor extension, it works only with
networking-midonet as the plugin.  However, if this extension becomes part of
neutron-dynamic-routing project, it will be expected to work with the reference
implementation, dr-agents.  There should be nothing in this design that should
interfere with the current implementation of dr-agents, including its HA
capabilities.


Data Model Impact
-----------------

'bgp_speaker_router_associations' table is created:

+-------------------+-------+-------------------------------------------+
| Attribute name    |  Type |  Description                              |
+-------------------+-------+-------------------------------------------+
| bgp_speaker_id    | uuid  | BGP speaker id                            |
+-------------------+-------+-------------------------------------------+
| router_id         | uuid  | Associated router                         |
+-------------------+-------+-------------------------------------------+

'bgp_speaker_id' is the primary key of the table.  Both 'bgp_speaker_id' and
'router_id' have foreign key constraints set to bgp_speakers and routers
tables, respectively.


REST API Impact
---------------

.. code-block:: python

  RESOURCE_ATTRIBUTE_MAP = {
    'bgp-speakers': {
        'logical_router': {'allow_post': True, 'allow_put': False,
                           'validate': {'type:uuid': None},
                           'is_visible': True, 'default': None},
    }
  }

Security Impact
---------------

None


Other End User Impact
---------------------

Neutron CLI provides support for 'logical_router' field as follows::

 neutron bgp-speaker-create [--tenant-id TENANT_ID] --local-as LOCAL_AS
                            [--ip-version {4,6}]
                            [--logical-router ROUTER]
                            NAME

 --logical-router ROUTER
     Router ID or name to associate BGP speaker with.


Performance Impact
------------------

None

IPv6 Impact
-----------

None

Other Deployer Impact
---------------------

None

Developer Impact
----------------

None


Documentation Impact
====================

MidoNet Operational Guide will be updated to include the new attribute added to
the BGP speaker model.

REFERENCES
==========

[1] https://docs.google.com/document/d/1cNIkY6zC9djKo2laFKN8JvAD8oHK87uNZMvt_81dQ7E/

