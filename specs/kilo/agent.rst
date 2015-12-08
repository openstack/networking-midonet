..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

=========
Agent API
=========

In a Neutron-MidoNet deployment, where numerous agents are running on various
hosts to provide services, it is important that the operators have a way to
view these agents to check their existence and health.  Neutron already
provides this feature with its 'agent' extension API [1].  This document
describes the design of the 'agent' extension API implementation by the MidoNet
Neutron plugin that provides this feature also for the MidoNet agents.


Problem Description
===================

There is currently no way to display the information about the MidoNet agents
that are deployed using the Neutron API.  Such information is useful for
operators to see their liveness and the location that they are deployed on.

Additionally, the operators need to find out the IDs of the agents, as well as
the IP addresses of the hosts that the agents are running on, to be able to
execute the 'agent_membership' API, where both of these values are needed in
the input.  Without executing the 'agent_membership' API, the MidoNet agents
cannot create tunnels among themselves, and VMs running on remote hosts would
not be able to connect to each other.


Proposed Change
===============

Implement the existing 'agent' Neutron extenion API in the MidoNet Neutron
plugin that provide (at the very least) the following:

 * Display all the MidoNet agents deployed, with the 'id' field indicating the
   globally unique identifier of each agent that can be used in the agent
   membership API
 * Show the IP addresses of the host that the agent is running on
 * Show the aliveness of the agents

The decision to provide these using the existing 'agent' Neutron extension as
opposed to creating a new vendor extension is that there are significant
overlaps between the two and the 'agent' extension provides integration with
Horizon and neutron CLI.

The following fields exist in the Neutron agent extension that MidoNet can
provide:

 * 'id': Unique identifier of the agent.
 * 'agent_type': Represents the type of the agent.  'Midonet agent' is the type
   for the MidoNet agents.
 * 'binary': Represents the package name.  For MidoNet, it is 'midolman'.
 * 'alive': Represents the liveness of the agent.
 * 'description': The description of the agent.  This is the only updatable
   field of the API.
 * 'configurations': A dictionary that includes configurations specific to the
   agent.  For MidoNet, this dictionary contains the IP addresses and the
   interfaces of the host::

        {
            "interfaces":
                [
                    {"name": INTERFACE_NAME, "ip_addresses": [IP_ADDRESSES]}
                ]
        }


Since the 'agent' API is designed with OpenStack agents in mind, however, there
are fields in the API that MidoNet cannot provide.

The following fields are not supported by the MidoNet plugin at the time of
this proposal:

 * 'host': The host name where the agent is running.  While this information is
   useful, it is not currently supported by MidoNet.
 * 'topic': AMQP message topic to communicate with the agent.  MidoNet agents
   do not support this.
 * 'admin_state_up': Sets the administrative status of the agent.  MidoNet does
   not support this. An attempt to update gets an 'unsupported' error response.
 * 'heartbeat_timestamp': The heartbeat for aliveness.  MidoNet agents do not
   provide this data.

MidoNet agents, when they spawn, report their existence to the MidoNet Network
State Database (NSDB).  NSDB is also notified when the agent goes down.  The
MidoNet Cluster, through its RPC service, exposes an API to provide this data
to the Neutron plugin.  The RPC API provides all the information the plugin
needs to populate the supported fields, and it also contains the most
up-to-date information of the agents' health.  Because all the required agent
information can be retrieved via the Cluster API on each Neutron's agent API,
Neutron's agents DB table does not need to be populated for the MidoNet agents.
The plugin is responsible for merging the OpenStack agent data and the MidoNet
agent data.

Lastly, deletion of agents, supported by Neutron API, is not supported by the
MidoNet plugin.  Unsupported exception is thrown when a user attempts to delete
an agent.


REST API
--------

No change except that some fields will be unsupported as explained above.


DB Model
--------

No change, and since all the MidoNet agent data are provided by MidoNe cluster,
the agents database table in Neutron will be unused.


Security
--------

No impact


Client
------

No code change is made, but 'neutron agent-delete` command is not supported
since the MidoNet plugin does not allow agent deletion.

See the Neutron CLI documentation for more details on the 'agent' commands[2].


References
==========

Because of the lack of API documentation available, the Neutron agent extension
API reference is its source code:

[1] https://github.com/openstack/neutron/blob/master/neutron/extensions/agent.py
[2] http://docs.openstack.org/cli-reference/content/neutronclient_commands.html
