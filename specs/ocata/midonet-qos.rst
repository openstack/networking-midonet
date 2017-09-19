..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=========================================
QoS implementaiton for networking-midonet
=========================================

This spec describes how to implement QoS extension for networking-midonet.
The backend side is covered by another spec. [#backend_design]_


Proposed Change
===============

QoS driver
~~~~~~~~~~

Use the Neutron QoS plugin as it is.  Implement MidoNet specific
notification driver which communicates with the MidoNet API.

::

    [DEFAULT]
    service_plugins = qos

    [qos]
    notification_drivers = midonet,message_queue

setup.cfg::

    neutron.qos.notification_drivers =
        midonet = midonet.neutron.services.qos.driver:MidoNetQosServiceNotificationDriver

Note: `message_queue` driver [#rpc_driver]_ is the AMQP RPC [#qos_rpc]_
based driver for the reference implementation.  It isn't necessary for
MidoNet-only deployments.

Neutron QoS plugin [#neutron_qos_plugin]_ has notification driver
mechansim [#driver_manager]_, which can be used for networking-midonet
to implement backend notifications.

When Neutron QoS plugin receives API requests, it updates the
corresponding DB rows.  After committing the DB changes, it calls
one of the following methods of the loaded notification drivers:

* create_policy

* update_policy

* delete_policy

Note: a request for a rule (eg. `update_policy_rule`) ends up with a
notification for the entire policy the rule belongs to.

Note: a request for a specific rule type (eg. `update_policy_dscp_marking_rule`)
are automatically converted to a generic method (eg. `update_policy_rule`)
by the QoS extension, namely `QoSPluginBase`.  [#method_proxy]_


Error handling
~~~~~~~~~~~~~~

Notification driver methods are considered async and always success.
[#bug_1627749]_
Currently there's no convenient way to report errors from the backend.
While it's possible for a driver to return an error by raising an
exception, if multiple drivers are loaded and one of them fails
that way, the rest of drivers are just skipped.  Even if we assume
the simplest case where only MidoNet QoS driver is loaded, there's
no mechanism to mark the resource error or rollback the operation.
There's an ongoing effort in Neutron [#qos_driver]_ in that area,
which might improve the situation.


Core resource extensions
~~~~~~~~~~~~~~~~~~~~~~~~

For ML2, the existing QoS extension driver should work.

If we want to make this feature available for the monolithic plugins,
the equivalent needs to be implemented for them.


Alternative
===========

Instead of the QoS driver, we can implement the entire QoS plugin by
ourselves.

::

    [DEFAULT]
    service_plugins = midonet_qos

setup.cfg::

    neutron.service_plugins =
        midonet_qos = midonet.neutron.services.qos.plugin:MidonetQosPlugin

This might fit the current backend design [#backend_design]_ better.

We can re-use the reference QoS plugin and its DB models by inheriting
its class.  It's a rather discouraged pattern these days, though.
This way the first implementation might be simpler.  But it might be
tricky to deal with other backends (consider ML2 heterogeneous deployments)
and future enhancements in Neutron.


References
==========

.. [#neutron_qos_plugin] https://github.com/openstack/neutron/blob/2be2d97d11719db88537a9664c95f1b6b11d3707/neutron/services/qos/qos_plugin.py

.. [#driver_manager] https://github.com/openstack/neutron/blob/2be2d97d11719db88537a9664c95f1b6b11d3707/neutron/services/qos/notification_drivers/manager.py

.. [#driver_base] https://github.com/openstack/neutron/blob/2be2d97d11719db88537a9664c95f1b6b11d3707/neutron/services/qos/notification_drivers/qos_base.py#L18

.. [#rpc_driver] https://github.com/openstack/neutron/blob/2be2d97d11719db88537a9664c95f1b6b11d3707/neutron/services/qos/notification_drivers/message_queue.py#L40

.. [#backend_design] https://review.gerrithub.io/#/c/289456/

.. [#method_proxy] https://github.com/openstack/neutron/blob/2be2d97d11719db88537a9664c95f1b6b11d3707/neutron/extensions/qos.py#L225

.. [#qos_rpc] https://docs.openstack.org/neutron/latest/contributor/internals/quality_of_service.html#rpc-communication

.. [#qos_driver] https://review.openstack.org/#/c/351858/

.. [#bug_1627749] https://bugs.launchpad.net/neutron/+bug/1627749
