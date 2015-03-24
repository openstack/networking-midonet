..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/


========
L2GW API
========

The L2GW extension API exposes a flexible way to allow implementers to map
logical gateways to the physical ones the way they see fit.  This API is about
logical gateways definition, intentionally leaving out the physical device
management.

L2GW API exposes the abstraction of L2 gateway with its interface(s). L2
gateway can expand over several devices with number of interfaces, and each
interface can be defined with different list of segmentation ids. Each device
is identified by meaningful name, and its possible to add/remove interfaces.

L2GW Binding API allows binding of logical gateway to an overlay network. In
the future logical gateway can be bound to the list of virtual networks.
Optionally, its possible to specify the default segmentation-id that will be
applied to the interfaces for which segmentation id was not specified in
l2-gateway-create command.

L2GW API allows to define logical GW that contains group of devices. In single
L2GW instance the administrator will define all VTEP devices that should be
used as single logical gateway either in Active-Passive or Active-Active mode.

Please refer to the upstream Stackforge project, 'network-l2gw'[1] for the API
DB and the client design.


Proposed Change
===============

Plugin
------

Add 'l2-gateway' extension alias in the supported extension aliases list.

MidoNet plugin should extend 'L2GatewayMixin' class, and implement the CRUD
methods for l2 gateway and l2 gateway connection objects.

New tasks representing the L2GW and L2GW Connection are inserted into the tasks
table in the appropriate CRUD operations.


REST API
--------

The upstream 'network-l2gw' API is re-used.


DB Model
--------

The upstream 'network-l2gw' DB tables are re-used.

New task types, 'L2GW' and 'L2GWCONNECTION', are introduced.


Client
------

The client commmands are the same as those defined in the 'network-l2gw'
project.


References
==========

[1] https://github.com/stackforge/networking-l2gw

