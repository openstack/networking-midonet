..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

=============================
Gateway Device Management API
=============================

MidoNet provides a Neutron extension API called Gateway Device Management to
provide device-level gateway management service to the operators.  This API is
required in order to propagate device connectivity details to enable Midonet to
manage VTEP Logical Switch configuration upon Logical Gateway definition.
Gateway Device Management API is required for management IP and Port settings.
Gateway device should be identified by user driven name in order to correlate
it with Logical Gateway entity.

VTEP status, VTEP configuration, such as Tunnel IP are out of the scope of
current version of this API.  MidoNet currently does not support secure
connection settings.


Proposed Change
===============

REST API
--------

**GatewayDevice**

+----------+-----------+-------+---------+------------------------------------+
|Attribute |Type       |CRUD   |Required |Description                         |
|Name      |           |       |         |                                    |
+==========+===========+=======+=========+====================================+
|id        |string     |CR     |generated|ID of the Gateway Device            |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|name      |string     |CRU    |No       |User defined device name            |
|          |           |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|manageme\ |string     |CR     |Yes      |Manangement IP of device            |
|nt_ip     |(ip addr)  |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|manageme\ |int        |CR     |Yes      |Management port of device           |
|nt_port   |           |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+

Currently, only the VTEP device is supported.


**GatewayDevicePeer**

To support Active Active Hardware VTEP, MidoNet has an API in place to set
peers of VTEP gateway devices.

+----------+-----------+-------+---------+------------------------------------+
|Attribute |Type       |CRUD   |Required |Description                         |
|Name      |           |       |         |                                    |
+==========+===========+=======+=========+====================================+
|id        |string     |CR     |generated|ID of the device peering            |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|name      |string     |CRU    |No       |User defined peering name           |
|          |           |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|device1_id|string     |CR     |Yes      |ID of the first device              |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|device2_id|string     |CR     |Yes      |ID of the second device             |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+


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
| management_ip     | String  | Management IP address of the gateway device   |
+-------------------+---------+-----------------------------------------------+
| management_port   | int     | Management port of the gateway device         |
+-------------------+---------+-----------------------------------------------+


**midonet_gateway_device_peers**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | String  | ID of the gateway peering                     |
+-------------------+---------+-----------------------------------------------+
| name              | String  | Name of the gateway peering                   |
+-------------------+---------+-----------------------------------------------+
| device1_id        | String  | ID of the first gateway device                |
+-------------------+---------+-----------------------------------------------+
| device2_id        | String  | ID of the second gateway device               |
+-------------------+---------+-----------------------------------------------+


Client
------

The following command creates a gateway device:

::
    neutron gateway-device-create [--name NAME] [--ip MGMT_IP]
                                  [--port MGMT_PORT]


The following command updates a gateway device:

::
    neutron gateway-device-update DEVICE_ID [--name NAME] [--ip MGMT_IP]
                                  [--port MGMT_PORT]


The following command views a gateway device:

::
    neutron gateway-device-show DEVICE_ID


The following command deletes a gateway device:

::
    neutron gateway-device-delete DEVICE_ID


The following command creates a gateway device peering:

::
    neutron gateway-device-peering-create [--name NAME] [--device1 DEV1]
                                          [--device2 DEV2]


The following command views a gateway device peering:

::
    neutron gateway-device-peering-show DEVICE_PEER_ID


The following command deletes (tears down) a gateway device peering:

::
    neutron gateway-device-peering-delete DEVICE_PEER_ID


Alternative Proposal
====================

Instead of managing Gateway devices using REST API, do so using configuration
files, which is the approach more familiar to those coming from Neutron
background.  The REST API approach was chosen to simplify and possibly automate
the gateway device management.
