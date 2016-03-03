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
In order to support Router Peering and Direct Connect use cases following definition
in [2]_, Overlay VTEP Router device is supported by MidoNet.
While for the routing functionality this device is managed as
traditional neutron Router, it should be possible for operator
(or Orchestration Layer) to enable its VTEP functionality.
While for HW VTEP Device this API is used for management IP and Port settings,
for Overlay VTEP Router Device it is used to enable Router with VTEP
Logical Switch management capability.


VTEP Tunnel IPs and Remote MAC Table management is currenly supported for the 'router_vtep'
type of gateway device only.

Other VTEP configurations as well as VTEP device status are out of the scope of
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
|tenant_id          |string    |CR    |Yes      |Tenant ID of gateway Device      |
|                   |          |      |         |object owner                     |
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
|type               |string    |CR    |No       |Type of the device: hw_vtep or   |
|                   |          |      |         |router_vtep. Defaults to hw_vtep |
+-------------------+----------+------+---------+---------------------------------+
|resource_id        |string    |CR    |No       |Resource UUID or None (for type  |
|                   |(UUID)    |      |         |router_vtep will be router UUID) |
+-------------------+----------+------+---------+---------------------------------+
|tunnel_ips         |string    |CRU   |No       |IP addresses on which gateway    |
|                   |(list of  |      |         |device originates or terminates  |
|                   |ip addrs) |      |         |tunnels.                         |
+-------------------+----------+------+---------+---------------------------------+
|remote_mac_entries |list of   |CR    |No       |Mapping of MAC addresses to the  |
|                   |entries   |      |         |tunnel IP addresses of the       |
|                   |          |      |         |corresponding VTEP               |
+-------------------+----------+------+---------+---------------------------------+

Currently, only the HW VTEP device and Router VTEP are supported.

Remote MAC Table entries are managed as sub-resource of the gateway_device.

**RemoteMac**

+-------------------+----------+------+---------+---------------------------------+
|Attribute          |Type      |CRUD  |Required |Description                      |
|Name               |          |      |         |                                 |
+===================+==========+======+=========+=================================+
|id                 |string    |CR    |generated|ID of the remote mac entry       |
|                   |(UUID)    |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+
|mac_address        |string    |CR    |Yes      |MAC address                      |
|                   |          |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+
|vtep_address       |string    |CR    |Yes      |Remote VTEP Tunnel IP to be used |
|                   |          |      |         |to reach this MAC address        |
+-------------------+----------+------+---------+---------------------------------+
|segmentation_id    |int       |CR    |Yes      |VNI to be used to reach this     |
|                   |          |      |         |MAC address                      |
+-------------------+----------+------+---------+---------------------------------+

REST API Impact
---------------

Proposed attributes::

        RESOURCE_ATTRIBUTE_MAP = {
            'gateway_devices': {
                'id': {'allow_post': False, 'allow_put': False,
                       'validate': {'type:uuid': None},
                       'is_visible': True, 'primary_key': True},
                'name': {'allow_post': True, 'allow_put': True,
                         'is_visible': True, 'default': '',
                         'validate': {'type:string': None}},
                'tenant_id': {'allow_post': True, 'allow_put': False,
                              'required_by_policy': True,
                              'is_visible': True},
                'management_ip': {'allow_post': True, 'allow_put': False,
                         'is_visible': True, 'default': ''},
                'management_port': {'allow_post': True, 'allow_put': False,
                         'is_visible': True, 'default': ''}'
                'management_protocol': {'allow_post': True, 'allow_put': False,
                         'is_visible': True, 'default': ''}'
                'type': {'allow_post': True, 'allow_put': False,
                         'is_visible': True, 'default': 'hw_vtep'},
                'resource_id': {'allow_post': True, 'allow_put': False,
                         'is_visible': True, 'default': None}'
                'tunnel_ips': {'allow_post': True, 'allow_put': True,
                         'is_visible': True, 'default': ''},
                'remote_mac_entries': {'allow_post': False, 'allow_put': False, 'is_visible': True},
            },
        }


        SUB_RESOURCE_ATTRIBUTE_MAP = {
            'remote_mac_entries': {
                'parent': {'collection_name': 'gateway_devices',
                           'member_name': 'gateway_device'},
            'parameters': {
                'id': {
                    'allow_post': False, 'allow_put': False,
                    'validate': {'type:uuid': None},
                    'is_visible': True}},
                'tenant_id': {'allow_post': True, 'allow_put': False,
                              'required_by_policy': True,
                              'is_visible': True},
                'vtep_address': {
                    'allow_post': True, 'allow_put': False,
                    'is_visible': True, 'default': None,
                    'validate': {'type:ip_address': None}},
                'mac_address': {
                    'allow_post': True, 'allow_put': False,
                    'is_visible': True,
                    'validate': {'type:mac_address':None}},
                'segmentation_id': {
                    'allow_post': True, 'allow_put': False,
                    'is_visible': True,
                    'validate': {'type:non_negative': None}},
            }
        }


Sample request/response:

Update Remote MAC Entry Request::

        POST /v2.0/gw/gateway_devices/46ebaec0-0570-43ac-82f6-60d2b03168c4/remote_mac_entries
        {
            "remote_mac_entry: {
                "mac_address": "10:20:30:40:50:60",
                "vtep_ip": "192.168.34.5",
                "segmentation_id": 304
            }
        }


        Response:
        {
            "remote_mac_entry": {
                "id": "5f126d84-551a-4dcf-bb01-0e9c0df0c793",
                "mac_address": "10:20:30:40:50:60",
                "vtep_ip": "192.168.34.5",
                "segmentation_id": 304
            }
        }


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
| type              | String  | Type of the gateway device (hw_vtep or        |
|                   |         | router_vtep)                                  |
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


**midonet_gateway_tunnel_ips**

+--------------------+---------+----------------------------------------------+
| Name               | Type    | Description                                  |
+====================+=========+==============================================+
| device_id          | String  | ID of the gateway device                     |
+--------------------+---------+----------------------------------------------+
| tunnel_ip          | String  | Tunnel IP to originate/terminate traffic     |
+--------------------+---------+----------------------------------------------+


**midonet_gateway_remote_mac_table**

+--------------------+---------+----------------------------------------------+
| Name               | Type    | Description                                  |
+====================+=========+==============================================+
| id                 | String  | ID of the entry                              |
+--------------------+---------+----------------------------------------------+
| device_id          | String  | ID of the gateway device                     |
+--------------------+---------+----------------------------------------------+
| mac_address        | String  | MAC address to be reached                    |
+--------------------+---------+----------------------------------------------+
| vtep_address       | String  | VTEP IP address to reach MAC address         |
+--------------------+---------+----------------------------------------------+
| segmentation_id    | int     | VNI to reach the MAC address                 |
+--------------------+---------+----------------------------------------------+

Client
------

The following command enables a gateway capabilities on the router device:

::

    neutron gateway-device-create [--name NAME] [--type router_vtep] [--resource-id UUID]


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
.. [2] https://docs.google.com/presentation/d/1b_lmDLF-i2rZlOGnZfYwZgim3W2BNf2rLWao3aULHC4/edit#slide=id.p
.. [3] https://docs.google.com/document/d/1QMcQ33L76c_igBomOAeH9yiiOJwJQ8QK7ZVV8-jrPVA/edit#
