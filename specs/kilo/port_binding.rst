..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

================
Port Binding API
================

In the MidoNet integration with OpenStack, there are two ways a port could be
bound:

 * When a VM is launched, orchestrated by nova
 * When an operator binds a virtual port to a specific host interface

This document describes the design of port binding in MidoNet that implements
these use cases.

In the case of operator-specified port binding, there is a special case in
which a port is bound to an interface connected to the uplink physical network,
but that is not covered in this document.


Problem Description
===================

MidoNet does not currently provide a way to bind ports in Neutron using
standard Neutron API.


Proposed Change
===============

Use the existing 'binding' extension API in Neutron to implement port binding
in MidoNet.

To bind a port to a specific host interface, an operator makes a 'create_port'
API request to Neutron and provide the following binding details:

 * 'binding:host_id': ID of the host to bind the port on
 * 'binding:profile["interface_name"]': Name of the interface to bind the port

The host ID is stored in the 'portbindings' table, and the interface name is
stored in the 'midonet_portbindings' table.  When the host ID and the interface
name are supplied in the port creation request, the MidoNet executes the
binding within the same API request.

Updating a port with a different binding effectively unbinds the port and
re-binds it to the new host interface.

In the case of VM port binding, the workflow is as follows:

 1. Nova API makes a 'create_port' request to Neutron API specifying the ID of
    the host('host_id') where the VM is going to be placed.  'host_id' is
    stored in Neutron's 'portbindings' table.

 2. Neutron generates the tap interface name the same way Nova does ('tap' +
    portID up to 14 chars), and stores it in the 'midonet_portbindings' table.

 3. On the compute host, 'mm-ctl' script is executed to do the actual binding.
    'mm-ctl' adds a port binding task to signal to MidoNet that the binding
    should occur.  This step may change in the future.

For each scenario in which a port binding occurs, the plugin inserts a
PORTBINDING task with 'resource_id' set to the ID of the port getting bound.

The actual mechanism in which the binding takes place inside MidoNet is outside
the scope of this document.


REST API
--------

An example of a port binding attributes in the request to create a port is::

  {
    "binding:host_id": "HOST_ID",
    "binding:profile": {"interface_name": "eth0"}
  }



DB Model
--------

**midonet_portbindings**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| port_id           | UUID    | ID of the port                                |
+-------------------+---------+-----------------------------------------------+
| interface_name    | String  | Name of the interface to bind the port        |
+-------------------+---------+-----------------------------------------------+

'port_id' is the primary key and has a foreign key constraint to the 'id' column
of the 'ports' table.


Client
------

The following command creates a port with port binding attributes:

::

    neutron port-create [--binding:host_id HOST_ID]
                        [--binding:profile if_name=IF_NAME]

--binding:host_id HOST_ID:
    ID of the host to bind the port on

--binding:profile if_name=IF_NAME:
    Name of the interface to bind the port to

