=============
MidoNet FWaaS
=============

FWaaS model provides two ways to implement its API:

 * Driver for the agent running on the network node
 * Full implementation of FWaaS plugin

Since MidoNet does not require the network nodes in deployment, the first
option is not viable.  The second option is possible but it turns out there is
a third way to do this which requires much less code.

Instead of implementing the entire FWaaS plugin, MidoNet FWaaS plugin defines
a driver, _MidonetFirewallDriver, that implements the RPC API that is
intended to be used for communicating with the firewall agent.

The API is simple:

::

  create_firewall(self, context, firewall)
  update_firewall(self, context, firewall)
  delete_firewall(self, context, firewall)

In each method, 'firewall' object contains both the firewall and the firewall
rules data.  In addition, 'firewall' object contains two useful lists,
'add-router-ids' and 'del-router-ids', representing the list of router IDs that
were associated and disassociated, respectively.  With such rich data as input,
these three methods are enough to implement all the FWaaS API.

One caveat is that because each request sends the entire set of rules, even if
the actual API operation did not modify the rules, the amount of data sent over
to MidoNet could sometimes be larger than it need to be.  This design will be
revisited if this causes problems.

States Reporting
================

When a firewall object is successfully created, the state is set to ACTIVE.  If
the object was created in Neutron but there was an error creating it in
MidoNet, the Neutron object is deleted.  If the deletion fails, the state is
set to PENDING_CREATE.  A successful creation includes both the top level
firewall object and its rules.

When a firewall object is successfully updated, the state is set to ACTIVE.  If
the update fails, the state is set to ERROR.  If the operation to set the ERROR
state fails, the state is set to PENDING_UPDATE.  A successful update includes
both the top level firewall object and its rules.

When a firewall object deletion fails, the state is set to ERROR.  If the
operation to set the ERROR state fails, the state is set to PENDING_DELETE.  A
successful deletion includes both the top level firewall object and its rules.
