..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

=======================================================
Gateway Device Management API update for Router Peering
=======================================================

https://blueprints.launchpad.net/networking-midonet/+spec/gw-device-api

MidoNet provides a Neutron extension API called Gateway Device Management to
provide device-level gateway management service to the operators.
This API is required in order to propagate device connectivity details to enable
Midonet to manage VTEP Logical Switch configuration upon Logical Gateway definition.
In order to support Router Peering use case, Overlay VTEP Router device is supported
by MidoNet. While for the routing functionality this device is managed as
traditional neutron Router, it should be possible for operator
(or Orchestration Layer) to enable its VTEP functionality.
While for HW VTEP Device this API is used for management IP and Port settings,
for Overlay VTEP Router Device it is used to enable Router with VTEP
Logical Switch management capability.

VTEP status, VTEP configuration, such as Tunnel IP are out of the scope of
the current version of this API.

Gateway device should be identified by the user driven name in order to correlate
it with Logical Gateway entity.


Proposed Change
===============
The following section provides details of the enhanced version of the
device management spec [1]_ with support for both HW VTEP and Overlay VTEP Router
as gateway devices.

REST API
--------

**GatewayDevice**

+-------------------+----------+------+---------+---------------------------------+
|Attribute          |Type      |CRUD  |Required |Description                      |
|Name               |          |      |         |                                 |
+===================+==========+======+=========+=================================+
|id                 |string    |CR    |generated|ID of the Gateway Device         |
|                   |(UUID)    |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+
|name               |string    |CRU   |No       |User defined device name         |
|                   |          |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+
|management_ip      |string    |CR    |No       |Management IP to the device.     |
|                   |(ip addr) |      |         |Defaults to None.                |
+-------------------+----------+------+---------+---------------------------------+
|management_port    |int       |CR    |No       |Management port to the device.   |
|                   |          |      |         |Defaults to None.                |
+-------------------+----------+------+---------+---------------------------------+
|management_protocol|string    |CR    |No       |Management protocol to manage    |
|                   |          |      |         |the device: ovsdb or none.       |
|                   |          |      |         |If management ip and port are    |
|                   |          |      |         |specified, defaults to ovsdb.    |
|                   |          |      |         |Otherwise to none.               |
+-------------------+----------+------+---------+---------------------------------+
|**type**           |string    |CR    |No       |Type of the device: hw_vtep or   |
|                   |          |      |         |router. Defaults to hw_vtep.     |
+-------------------+----------+------+---------+---------------------------------+
|**resource_id**    |string    |CR    |No       |Resource UUID or None (for type  |
|                   |(UUID)    |      |         |router will be router UUID).     |
+-------------------+----------+------+---------+---------------------------------+

Currently, only the HW VTEP device and Router are supported.


DB Model
--------

**midonet_gateway_devices**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | String  | ID of the gateway device                      |
+-------------------+---------+-----------------------------------------------+
| name              | String  | Name of the gateway device                    |
+-------------------+---------+-----------------------------------------------+
| type              | String  | Type of the gateway device (hw_vtep or router)|
+-------------------+---------+-----------------------------------------------+


**midonet_gateway_hw_vtep_devices**

+--------------------+---------+----------------------------------------------+
| Name               | Type    | Description                                  |
+====================+=========+==============================================+
| device_id          | String  | ID of the gateway device                     |
+--------------------+---------+----------------------------------------------+
| management_ip      | String  | Management IP address of the gateway device  |
+--------------------+---------+----------------------------------------------+
| management_port    | int     | Management port of the gateway device        |
+--------------------+---------+----------------------------------------------+
| management_protocol| String  | Management protocol of the gateway device    |
+--------------------+---------+----------------------------------------------+


**midonet_gateway_overlay_router_devices**

+--------------------+---------+----------------------------------------------+
| Name               | Type    | Description                                  |
+====================+=========+==============================================+
| device_id          | String  | ID of the gateway device                     |
+--------------------+---------+----------------------------------------------+
| resource_id        | String  | Router UUID enabled as gateway device        |
+--------------------+---------+----------------------------------------------+


Client
------

The following command enables a gateway capabilities on the router device:

::

    neutron gateway-device-create [--name NAME] [--type router] [--resource-id UUID]


The following command creates a HW VTEP gateway device:

::
    neutron gateway-device-create [--name NAME] [--type hw_vtep] [--ip MGMT_IP]
                                  [--port MGMT_PORT]


The following command updates a gateway device:

::

    neutron gateway-device-update GW_DEVICE_ID [--name NAME]


The following command lists gateway devices:

::

    neutron gateway-device-list


The following command views a gateway device:

::

    neutron gateway-device-show GW_DEVICE_ID


The following command deletes a gateway device:

::

    neutron gateway-device-delete GW_DEVICE_ID


References
==========
.. [1] https://raw.githubusercontent.com/openstack/networking-midonet/master/specs/kilo/device_management.rst
