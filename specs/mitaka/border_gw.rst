..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/


=============
Border GW API
=============

https://blueprints.launchpad.net/networking-midonet/+spec/border-gw-api-for-midonet

Border GW is term for enhanced L2GW that should enable inter-site connectivity.

Current L2GW API
--------------------

The L2GW extension API defined in networking-l2gw [1]_ exposes the abstraction of
L2 gateway with its interface(s). L2 gateway can expand over several devices with
number of interfaces, and each interface can be defined with different list of
segmentation ids. Each device is identified by meaningful name, and its possible
to add/remove interfaces.
L2GW Binding API allows binding of logical gateway to an overlay network.
L2GW API allows to define logical GW that contains group of devices. In single
L2GW instance the administrator will define all VTEP devices that should be
used as single logical gateway either in Active-Passive or Active-Active mode.

Border GW API
-------------
Border GW funtionality is required for multi-site deployment. It should connect
Tenant's overlay networks across sites. It will use dedicated Tunnel that connects
Tenant networks across sites. L2GW abstract model fits very well into Border GW case.
Current L2GW API imposes limitation that should be released in order to
support Border GW use case. It should be possible to create L2GW specifing device
and segmentation_id, without specific interface name. Interface name is not necessary
for the Border GW use case since scope of segmentation_id is global.

In order to support Border GW as well as L2GW abstraction API, the gateway device
should be defined in the MidoNet model. Gateway Device should be defined via
device-management API [2]_ in order to be confirmed by L2GW API at L2GW instance creation.


Proposed Change
===============

Plugin
------

MidoNet l2gw (border gw) driver should be added to be loaded and used by l2gw service
plugin to support 'l2-gateway' extension in MidoNet.

MidoNet l2gw driver should provide its own 'L2Gateway' API validation method to apply Border GW API
validation for CRUD methods for l2 gateway and l2 gateway connection objects.
Logical Gateway device will be defined by using device_id of the Gateway Device and segmentation_id.


REST API
--------

The upstream 'networking-l2gw' API is re-used.

To create logical border gateway, following format can be used:

JSON Request

::

    POST /v2/l2-gateways
    Content-Type: application/json
    {"l2_gateway": {"name": "<gateway-name>",
                    "devices": [{"device_id": "<device-id1>",
                                 "segmentation-id": <seg-id1>}]
                                }}


Response:

::

    {"l2_gateway": {"name": "<gateway-name>",
                    "tenant_id": "7ea656c7c9b8447494f33b0bc741d9e6",
                    "devices": [{"device_id": "<device-id1>",
                                 "segmentation-id": <seg-id1>}],
                    "id": "d3590f37-b072-4358-9719-71964d84a31c"}}

DB Model
--------

The upstream 'networking-l2gw' DB tables are re-used.


Client
------

Currenlty supports MidoNet l2gw creation CLI that is different from that of the upstream 'networking-l2gw'.

The following command create a l2 gateway:

::

    neutron midonet-l2-gateway-create GATEWAY-NAME [--device device_id=DEVICE_ID,segmentaion_id=SEGMENTAION_ID]


Other Deployer Impact
---------------------

If L2 gateway service is to be enabled, then it is required to configure
the L2 gateway service plugin in neutron.conf.

/etc/neutron.conf:
service_plugins=l2gw

Provider driver should be specified,
service_provider=L2GW:l2gw:<driver>


References
==========

.. [1] https://github.com/openstack/networking-l2gw
.. [2] https://blueprints.launchpad.net/networking-midonet/+spec/gw-device-api
