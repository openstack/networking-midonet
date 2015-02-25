..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

====================
Agent Membership API
====================

In MidoNet, each MidoNet agent must be 'activated' in order to join the
MidoNet deployment.  This step ensures that no rogue MidoNet agent
automatically joins the MidoNet deployment. This document describes the
'agent-membership' Neutron extension API that provides this feature.


Problem Description
===================

In the previous MidoNet API, the authorization step to allow a MidoNet
agent to be activated in the deployment was to add it to a tunnel zone.

This was undesirable because it required explicit tunnel zone coniguration using
the API, and in an OpenStack-MidoNet deployment, there was no use case known or
supported that requires more than one tunnel zone to exist.  By forcing users
to create a tunnel zone and adding individual hosts to them, it was creating
unnecessary potential failure points without adding any value.


Proposed Change
===============

Maintain a singleton default Tunnel Zone, with the name, "DEFAULT", in the
system.  This tunnel zone is created automatically  by the Neutron plugin if it
does not exist yet and it is completely hidden from the user.  When a tunnel
zone is created, it is created in the Neutron DB and also forwarded to the
cluster over the tasks table.

The default tunneling protocol used is 'vxlan'.  If you want to override it,
specified the following in neutron.conf:

[MIDONET]
tunnel_protocol=vxlan  # Could be vxlan or gre

When Neutron restarts, it inspects this value and updates the tunnel zone by
updating both the Neutron DB record and also by submitting this task to the
cluster.

To authorize an agent to be added to the deployment, 'agent-membership' Neutron
extension API described below is used.


REST API
--------

**AgentMembership**

+----------+-----------+-------+---------+------------------------------------+
|Attribute |Type       |POST/  |Required |Description                         |
|Name      |           |PUT    |         |                                    |
+==========+===========+=======+=========+====================================+
|id        |string     |POST   |generated|identity                            |
|          |(UUID)     |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+
|agent_id  |string     |POST   |Yes      |Id of the agent to add to           |
|          |(UUID)     |       |         |membership                          |
+----------+-----------+-------+---------+------------------------------------+
|ip_address|string     |POST   |Yes      |IP address to use for tunneling     |
|          |           |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+


Only POST and DELETE operations are permitted, and only admin can execute
them.

Only IPv4 address is supported for 'ip_address'.


DB Model
--------

**TunnelZone**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | TinyInt | Unique identifier of tunnel zone              |
+-------------------+---------+-----------------------------------------------+
| name              | String  | Name of the tunnel zone                       |
+-------------------+---------+-----------------------------------------------+
| type              | String  | Tunnel protocol type.                         |
+-------------------+---------+-----------------------------------------------+

The supported values for 'type' are:

 * VXLAN (default)
 * GRE


**TunnelZoneHost**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | TinyInt | Unique identifier of membership               |
+-------------------+---------+-----------------------------------------------+
| host_id           | String  | ID of the host (same as agent)                |
+-------------------+---------+-----------------------------------------------+
| tunnel_zone_id    | String  | ID of the tunnel zone                         |
+-------------------+---------+-----------------------------------------------+
| ip_address        | String  | IP address to use for tunneling               |
+-------------------+---------+-----------------------------------------------+

Only IPv4 address is supported for 'ip_address'.

We are keeping the legacy API names, TunnelZone and TunnelZoneHost because
the cluster still expects these names.

New task types are:

 * tunnel_zone
 * tunnel_zone_host


Security
--------

Only admins are allowed to execute the agent-membership API.  This explicit
step to add each agent as a member provides an extra layer of security to
prevent unwanted agents to join automatically.


Client
------

The following command lists all the memberships:

::
    neutron agent-membership-list [-h] [-P SIZE] [--sort-key FIELD]
                                  [--sort-dir {asc, desc}]
-h, --help::
    show the help message

-P SIZE, --page-size SIZE::
    Specify retrieve unit of each request

--sort-key FIELD::
    Sorts the list by the specified fields

--sort-dir {asc,desc}::
    Sorts the list in the specified direction


The following command adds an agent to the MidoNet deployment membership:

::
    neutron agent-membership-create [-h] [--agent-id AGENT]
                                    [--ip-address IP_ADDRESS]

-h, --help::
    show the help message

-a, --agent-id::
    Specify the ID of the agent to add to membership

-a, --ip-address
    Set IP address to use for tunneling


The following command removes an agent from the MidoNet deployment membership:

::
    neutron agent-membership-delete [-h] AGENT_MEMBERSHIP

AGENT_MEMBERSHIP::
    ID of the agent membership to remove

