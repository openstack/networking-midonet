..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

================
Extra Routes API
================

This document describes MidoNet's implementation of extra routes Neutron
extension API.


Problem Description
===================

MidoNet plugin has not implemented extra routes extension API, and without it,
MidoNet's routing table management feature could not be exposed.


Proposed Change
===============

MidoNet plugin implements the extra routes extension. Current design of extra
routes, however, only contains 'destination' and 'nexthop' fields, representing
the destination CIDR to match on the packet and the next hop gateway IP
address.  MidoNet plugin extends the current extra route API to add more fields
in the route model to provide more detailed management of the routing table.


Plugin
------

Add 'extraroute' in the supported_extension_aliases list.

Extend 'extraroute' extension and add a 'source' field, and validate 'source'
the same way 'destination' is validated.


REST API
--------

**Router**

Extra routes extension adds the 'routes' field in the router requests and
responses, which is a list of route objects where each route consists of:

+----------+-----------+-------+---------+------------------------------------+
|Attribute |Type       |POST/  |Required |Description                         |
|Name      |           |PUT    |         |                                    |
+==========+===========+=======+=========+====================================+
|destinat\ |string     |PUT    |Yes      |CIDR to match on the packet's       |
|ion       |(CIDR)     |       |         |destination ip                      |
|          |           |       |         |                                    |
|          |           |       |         |Default: 0.0.0.0/0                  |
+----------+-----------+-------+---------+------------------------------------+
|source    |string     |PUT    |No       |CIDR to match on the packet's source|
|          |(CIDR)     |       |         |ip                                  |
|          |           |       |         |                                    |
|          |           |       |         |Default: 0.0.0.0/0                  |
+----------+-----------+-------+---------+------------------------------------+
|nexthop   |string     |PUT    |Yes      |IP of the next hop gateway          |
|          |(CIDR)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+


DB Model
--------

**AdvancedExtraRoute**

table name: midonet_router_routes

'router_routes' table in Neutron is used to store the extra routes.  In
addition, to store the midonet-specific field, 'source',
'midonet_router_routes' table is introduced:

+-------------------+------------+--------------------------------------------+
| Name              | Type       | Description                                |
+===================+============+============================================+
| source            | String(64) | Source CIDR to match on                    |
+-------------------+------------+--------------------------------------------+
| router_id         | String(36) | ID of the router the route belongs to      |
+-------------------+------------+--------------------------------------------+

'router_id' has a foreign key constraint defined for 'id' column of the
'routers' table.


Client
------

The CLI command to update a router accepts the following new argument:

::
    neutron router-update ROUTER_ID --routes type=dict list=true
                                    [--source SOURCE]

--source SOURCE:
    source CIDR of the route


Documentation
-------------

Operational Guide must be updated to explain the 'source' field added in the
extra route extension.
