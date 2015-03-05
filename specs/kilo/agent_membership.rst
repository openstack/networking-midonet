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
system.  This tunnel zone is created automatically by the MidoNet cluster.
The Neutron plugin signals the cluster to do create it when it starts up by
submitting a new task type, CONFIG.

CONFIG task contains all the global configuration values settable in Neutron
that MidoNet would find useful.  The handling of the case in which the cluster
fails to process this task is outside the scope of this proposal, and it is
assumed that CONFIG task is treated the same as any other tasks.

For this particular change, only one new field is introduced in CONFIG, which
is 'tunnel_protocol', that indicates the global tunneling protocol that MidoNet
should use.   This value is used by MidoNet to create the singleton Tunnel
Zone.  The default tunneling protocol used is 'vxlan', but you can override it
by specifying the following in neutron.conf:

[MIDONET]
tunnel_protocol=gre  # Could be vxlan or gre

With this approach, the concept of  Tunnel Zone is completely hidden from the
user as well as from the neutron implementation.

To authorize an agent to be added to the deployment, 'agent-membership' Neutron
extension API described below is defined.


REST API
--------

**AgentMembership**

+----------+-----------+-------+---------+------------------------------------+
|Attribute |Type       |POST/  |Required |Description                         |
|Name      |           |PUT    |         |                                    |
+==========+===========+=======+=========+====================================+
|id        |string     |POST   |generated|ID of the MidoNet agent, which maps |
|          |(UUID)     |       |         |to hostId in cluster                |
+----------+-----------+-------+---------+------------------------------------+
|ip_address|string     |POST   |Yes      |IP address to use for tunneling     |
|          |           |       |         |                                    |
+----------+-----------+-------+---------+------------------------------------+


Only POST and DELETE operations are permitted, and only admin can execute
them.

Only IPv4 address is supported for 'ip_address'.

'id' field is the ID of the MidoNet 'host' object, which you can retrieve using
the 'agent' API extension of Neutron (not implemented yet).  The agents and the
MidoNet hosts map one-to-one.  Likewise, the 'agent' API will also include the
host interfaces and their IP addresses, useful to populate the 'ip_address'
field for the agent membership API.


DB Model
--------

**midonet_agent_membership**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | String  | ID of the agent (same as host in the cluster) |
+-------------------+---------+-----------------------------------------------+
| ip_address        | String  | IP address to use for tunneling               |
+-------------------+---------+-----------------------------------------------+

Only IPv4 address is supported for 'ip_address'.

New task types are:

 * CONFIG: Represents global Neutron configurations
 * AGENTMEMBERSHIP: Represents AgentMembershp resource


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

