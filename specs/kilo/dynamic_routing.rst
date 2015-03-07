..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

=======================
Dynamic Routing Service
=======================

The MidoNet Neutron plugin, through Neutron's advanced service framework,
provides the dynamic routing feature on the provider router.

MidoNet currently only supports BGP but it will also support OSPF in the
future.  The API design attempts to abstract away the underlying routing
protocol.


Problem Description
===================

With the dynamic routing service, an OpenStack cloud would run a routing
protocol (for example, BGP) against at least one router in each uplink network
provider.  By announcing external network hosting floating IP prefixes to those
peers, the Neutron network would be reachable by the rest of the internet
via both paths. If the link to an uplink provider broke, the failure
information would propagate to routers further up the stream, keeping the cloud
reachable through the remaining healthy link.  Likewise, in such a case,
Neutron would eliminate the routes learned through the faulty link from its
forwarding table, redirecting all cloud-originated traffic through the healthy
link.

Without dynamic routing, the scenario described above would not be possible.


Proposed Change
===============

Three new models are introduced.

RoutingInstance is the top level object that abstracts a dynamic routing
service (such as BGP, OSFP).  When configured, the dynamic routing service is
enabled on the router that it is associated with.

RoutingPeer is the peering configuration applied on the router port that you
want to start the peering session from.  Since RoutingPeers are associated with
ports, there would be multiple RoutingPeers for a given RoutingInstance.

AdvertiseRoute is the route advertised with dynamic routing.  In Neutron,
Floating IP could be advertised to the outside of OpenStack cloud by creating
an AdvertiseRoute object for that CIDR.

In MidoNet, routes learned from the peer are inserted into the routing table of
the router, and this proposal does not affect this mechanism.


REST API
--------

**RoutingInstance**

+----------+-----------+-------+---------+------------------------------------+
|Attribute |Type       |POST/  |Required |Description                         |
|Name      |           |PUT    |         |                                    |
+==========+===========+=======+=========+====================================+
|id        |string     |POST   |generated|ID of the routing instance          |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|router_id |string     |POST   |Yes      |Router that the routing service is  |
|          |(UUID)     |       |         |attached to                         |
+----------+-----------+-------+---------+------------------------------------+
|local_as  |int        |POST   |Yes      |Local AS number used in BGP         |
+----------+-----------+-------+---------+------------------------------------+
|protocol  |string     |       |No       |Routing protocol to use.            |
|          |           |       |         |Only BGP supported, so cannot be    |
|          |           |       |         |updated.                            |
+----------+-----------+-------+---------+------------------------------------+


Deleting the routing instance deletes all the advertise routes and routing
peers.  'loopback address' feature is not included in this spec, but will be
added in the future.  Also, while the models proposed are meant to abstract
away all the dynamic routing protocols, because MidoNet only handles BGP right
now, they only include BGP-specific fields.

A router that has a routing instance associated cannot be deleted, and you must
delete the routing instance first.

A router could have only one routing instance associated.


**RoutingPeer**

+----------+-----------+-------+---------+------------------------------------+
|Attribute |Type       |POST/  |Required |Description                         |
|Name      |           |PUT    |         |                                    |
+==========+===========+=======+=========+====================================+
|id        |string     |POST   |generated|ID of the routing peer              |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|routing_i\|string     |POST   |Yes      |Routing instance it is associated   |
|nstance_i\|(UUID)     |       |         |with                                |
|d         |           |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|port_id   |string     |POST   |Yes      |Port used to connect to the peer    |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|peer_as   |int        |POST   |Yes      |Peer AS number used in BGP          |
+----------+-----------+-------+---------+------------------------------------+
|peer_addr\|string     |POST   |Yes      |Peer IP address                     |
|ess       |           |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+

Only IPv4 is supported for 'peer_address'.  In this proposal, the support for
establishing connections with peers that do not have an IP address is not
included.

Deleting a routing instance deletes the associated routing peers.


**AdvertiseRoute**

+------------+--------+------+---------+--------------------------------------+
|Attribute   |Type    |POST/ |Required |Desciption                            |
|Name        |        |PUT   |         |                                      |
+============+========+======+=========+======================================+
|id          |string  |POST  |generated|Unique Identifier for route           |
|            |(UUID)  |      |         |configuration                         |
+------------+--------+------+---------+--------------------------------------+
|routing_ins\|string  |POST  |Yes      |ID of the routing instance the route  |
|tance_id    |(UUID)  |      |         |is associated with                    |
+------------+--------+------+---------+--------------------------------------+
|destination |string  |POST  |No       |Value to compare with the destination |
|            |        |      |         |IP address of the flow being forwarded|
|            |        |      |         |Default: 0.0.0.0/32                   |
+------------+--------+------+---------+--------------------------------------+

Only IPv4 is supported for `destination`.

Deleting a routing instance deletes the associated advertise routes.


DB Model
--------

**midonet_routing_instances**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | String  | ID of the routing instance                    |
+-------------------+---------+-----------------------------------------------+
| router_id         | String  | ID of the router the routing instance is      |
|                   |         | attached to                                   |
+-------------------+---------+-----------------------------------------------+
| local_as          | Int     | Local AS number                               |
+-------------------+---------+-----------------------------------------------+
| protocol          | String  | Routing protocol                              |
+-------------------+---------+-----------------------------------------------+

The only supported value for 'protocol' is 'BGP', but 'OSPF' will be added in
the future.


**midonet_routing_peers**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | String  | ID of the routing peer                        |
+-------------------+---------+-----------------------------------------------+
| routing_instance\ | String  | ID of the routing instance associated         |
| _id               |         |                                               |
+-------------------+---------+-----------------------------------------------+
| port_id           | String  | ID of the port for the peer connection        |
+-------------------+---------+-----------------------------------------------+
| peer_as           | Int     | Peer AS number used for BGP                   |
+-------------------+---------+-----------------------------------------------+
| peer_address      | String  | Peer IP address                               |
+-------------------+---------+-----------------------------------------------+


**midonet_advertise_route**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | String  | ID of the route                               |
+-------------------+---------+-----------------------------------------------+
| routing_instance\ | String  | ID of the routing instance associated         |
| _id               |         |                                               |
+-------------------+---------+-----------------------------------------------+
| destination       | String  | destination CIDR to match on                  |
+-------------------+---------+-----------------------------------------------+


**midonet_tasks**

New task data types are introduced:

 * ROUTING_INSTANCE
 * ROUTING_PEER
 * ADVERTISE_ROUTE


Security
--------

For this proposal, dynamic routing configuration is limited to admins only.


Client
------

The following command creates a routing instance:

::
    neutron routing-instance-create [--router-id ROUTER_ID]
                                    [--local-as LOCAL_AS]

--router-id ROUTER_ID::
    ID of the router to associate with

--local-as LOCAL_AS::
    The local AS number


The following command gets a routing instance:

::
    neutron routing-instance-show ROUTING_INSTANCE_ID

ROUTING_INSTANCE_ID::
    ID of the routing instance to look up


The following command lists all the routing instances of a tenant:

::
    neutron routing-instance-list


The following command associates a routing instance to a router:

::
    neutron routing-instance-associate [--router-id ROUTER_ID]
                                       ROUTING_INSTANCE_ID
ROUTING_INSTANCE_ID::
    ID of the routing instance to look up

--router-id ROUTER_ID::
    ID of the router to associate with


The following command disassociates a routing instance from a router:

::
    neutron routing-instance-disassociate ROUTING_INSTANCE_ID

ROUTING_INSTANCE_ID::
    ID of the routing instance to look up


The following command deletes a routing instance:

::
    neutron routing-instance-delete ROUTING_INSTANCE_ID

ROUTING_INSTANCE_ID::
    ID of the routing instance to look up


The following command creates a routing peer:

::
    neutron routing-peer-create [--routing-instance-id ROUTING_INSTANCE_ID]
                                [--port-id PORT_ID]
                                [--peer-as PEER_AS]
                                [--peer-address PEER_ADDRESS]

--routing_instance_id ROUTING_INSTANCE_ID::
    ID of the routing instance to create the routing peer for

--port-id PORT_ID::
    ID of the port to connect to peer from

--peer-as PEER_AS::
    Peer AS number for BGP

--peer-address PEER_ADDRESS::
    Peer IP address


The following command deletes a routing peer:

::
    neutron routing-peer-delete ROUTING_PEER_ID

ROUTING_PEER_ID::
    ID of the routing peer to delete


The following command gets a routing peer:

::
    neutron routing-peer-get ROUTING_PEER_ID

ROUTING_PEER_ID::
    ID of the routing peer to look up


The following command lists all the routing peers of a tenant:

::
    neutron routing-peer-list


The following command creates an advertise route:

::
    neutron advertise-route-create [--routing-instance-id ROUTING_INSTANCE_ID]
                                   [--destination DESTINATION]

--routing_instance_id ROUTING_INSTANCE_ID::
    ID of the routing instance to create the advertse route for

--destination DESTINATION::
    destination CIDR of the route


The following command delets an advertise route:

::
    neutron advertise-route-delete ADVERTISE_ROUTE_ID

ADVERTISE_ROUTE_ID::
   ID of the advertise route to delete


The following command gets an advertise route:

::
    neutron advertise-route-get ADVERTISE_ROUTE_ID

ADVERTISE_ROUTE_ID::
   ID of the advertise route to look up


The following command lists all the advertise routes of a tenant:

::
    neutron advertise-route-list

