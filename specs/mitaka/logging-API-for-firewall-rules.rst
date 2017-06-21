..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/

==============================
Logging API for firewall-rules
==============================

This document describes MidoNet's implementation of
logging for firewall rules.

FWaaS v2.0 [2]_ will be implemented in newton,
However, first of all we implement MidoNet for mitaka with FWaaS v1.0
because development schedule between
networking-midonet and neutron does not match.

Note that eventually we aim to unify this spec and spec for upstream [1]_.
Thus, this spec is written following spec for upstream.
In addition, we should keep on watch spec for upstream because
the spec have not completed yet.

Problem Description
===================

Operator wants to
  * monitor network traffic in system to detect illegal traffic,
    or to solve unexpected communication error across L3.
  * pass audit for system.

Tenant wants to
  * monitor network traffic in tenant to detect illegal traffic,
    or to solve unexpected communication error across L3.
  * pass audit for tenant

In Neutron, traffic accepted/denied on routers are managed by FWaaS.
However, logging is currently a missing feature in FWaaS.
Thus, requirements above cannot be satisfied.

Proposed Change
===============

The scope of this spec:

* logging API for operator and tenant.
* logging format for operator and tenant.

How tenants can consume outputted logs are out of scope.
Logging format that will be sent to tenants are out of scope.
Where the logs are generated is also out of scope.

Plugin
------

Add 'logging-resource' extension alias in the supported extension aliases list.

MidoNet plugin implement the CRUD methods for logging resource and firewall log
objects.

Expected API behavior
---------------------

The events related to firewall rules will collect:

    (1) ACCEPT event
    (2) DROP event

Operators and tenants can specify what kind of events they want to log.
Note that only logging of firewall rules that are created explicitly are gathered.

    (1) ACCEPT/DROP or ALL (collect all ACCEPT/DROP events of firewalls).
    (2) firewall uuid.

REST API
--------

In this spec, two resources are newly defined.

LoggingResource is root resource for logging.
This model defines policy of logging.
e.g. how can we see logs, where logs are going to be collected.

FirewallLog is logging resource for specific resource.
Though this spec proposes only FWaaS, many logging resources for
specific resource will be supported in the future. (e.g. security group)

In addition, firewall can be associated with multiple logging resource only when the
tenant_ids are different to allow operators and tenants to specify same firewall
as logging resource.
This allows operators to gather log in all of system.

Note that there is no difference in outputted format between tenant's logging
resource and operator's logging resource.
If operator wants to operate description above, some validations are needed to
solve why the log is outputted.

The rough sketch that contains future consideration is following;

::

    TenantA---------LoggingResourceA------FirewallLogA-----------
                           |                                    |
                           |--------------SecurityGroupLogA     |------firewallA
                                                                |
    AdminTenant-----LoggingResourceB------FirewallLogB-----------
                           |
                           |--------------FirewallLogC
                           |
                           |--------------SecurityGroupLogB


**LoggingResource**

+-------------------+----------+------+---------+---------------------------------+
|Attribute          |Type      |CRUD  |Required |Description                      |
|Name               |          |      |         |                                 |
+===================+==========+======+=========+=================================+
|id                 |string    |CR    |generated|ID of the LoggingResource        |
|                   |(UUID)    |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+
|name               |string    |CRU   |No       |Defined LoggingResource name     |
+-------------------+----------+------+---------+---------------------------------+
|description        |string    |CRU   |No       |Description for the              |
|                   |          |      |         |LoggingResource                  |
+-------------------+----------+------+---------+---------------------------------+
|tenant_id          |string    |CR    |No       |Tenant ID of LoggingResource     |
|                   |          |      |         |object owner                     |
+-------------------+----------+------+---------+---------------------------------+
|enabled            |string    |CRU   |No       |Enable/disable for               |
|                   |          |      |         |the LoggingResource.             |
|                   |          |      |         |log is gathered only when        |
|                   |          |      |         |this flag is enable.             |
+-------------------+----------+------+---------+---------------------------------+

**FirewallLog**

+-------------------+----------+------+---------+---------------------------------+
|Attribute          |Type      |CRUD  |Required |Description                      |
|Name               |          |      |         |                                 |
+===================+==========+======+=========+=================================+
|id                 |string    |CR    |generated|ID of the FirewallLog            |
|                   |(UUID)    |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+
|description        |string    |CRU   |No       |Description for FirewallLog      |
|                   |          |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+
|tenant_id          |string    |CR    |No       |Tenant ID of FirewallLog         |
|                   |          |      |         |object owner                     |
+-------------------+----------+------+---------+---------------------------------+
|fw_event           |string    |CRU   |No       |Event of firewall.               |
|                   |          |      |         |ACCEPT/DROP/ALL can be           |
|                   |          |      |         |specified. ALL is set as default.|
+-------------------+----------+------+---------+---------------------------------+
|firewall_id        |string    |CR    |Yes      |ID of firewall instance          |
|                   |(UUID)    |      |         |                                 |
+-------------------+----------+------+---------+---------------------------------+

API list is as follows.
Note that api path prefix 'logging' may conflict with upstream.
However, we keep this prefix to keep consitency with upstream.
To avoid confusion, we should do following things.

  * Separate our plugin configuration from upstream.
  * Note to user that not to use both plugins together.

+-----------------+-------------------------------------------------------+-------+
|Object           |URI                                                    |Type   |
+=================+=======================================================+=======+
|logging-resource |/logging/logging_resources                             |POST   |
+-----------------+-------------------------------------------------------+-------+
|logging-resource |/logging/logging_resources                             |GET    |
+-----------------+-------------------------------------------------------+-------+
|logging-resource |/logging/logging_resources/{id}                        |GET    |
+-----------------+-------------------------------------------------------+-------+
|logging-resource |/logging/logging_resources/{id}                        |DELETE |
+-----------------+-------------------------------------------------------+-------+
|logging-resource |/logging/logging_resources/{id}                        |PUT    |
+-----------------+-------------------------------------------------------+-------+
|firewall-log     |/logging/logging_resources/{id}/firewall_logs          |POST   |
+-----------------+-------------------------------------------------------+-------+
|firewall-log     |/logging/logging_resources/{id}/firewall_logs          |GET    |
+-----------------+-------------------------------------------------------+-------+
|firewall-log     |/logging/logging_resources/{id}/firewall_logs/{id}     |GET    |
+-----------------+-------------------------------------------------------+-------+
|firewall-log     |/logging/logging_resources/{id}/firewall_logs/{id}     |DELETE |
+-----------------+-------------------------------------------------------+-------+
|firewall-log     |/logging/logging_resources/{id}/firewall_logs/{id}     |PUT    |
+-----------------+-------------------------------------------------------+-------+

REST API Examples
-----------------

To Create a LoggingResource to manage security event log,
following API can be used:

JSON Request

::

    POST /v2.0/logging/logging_resources
    {
        "logging_resource": {
            "name": "firewall_log",
            "description": "Get traffic flow of firewall",
            "enabled": True
         }
    }

Response:

::

    Response:
    {
       "logging_resource": {
           "id": "46ebaec0-0570-43ac-82f6-60d2b03168c4",
           "tenant_id": "8d4c70a21fed4aeba121a1a429ba0d04",
           "name": "firewall_log",
           "description": "Get traffic flow of firewall",
           "enabled": True
       }
    }

To Create a FirewallLog to collect security event of the firewall,
following API can be used:

JSON Request

::

    POST /v2.0/logging/logging_resources/46ebaec0-0570-43ac-82f6-60d2b03168c4/firewall_logs
    {
        "firewall_log": {
            "description": "Collecting all traffic passing the firewall",
            "fw_event": "ALL",
            "firewall_id: "21aeda2a-a52f-4e81-9e64-7edeb59fa25b"
        }
    }

Response:

::

    {
    "firewall_log": {
        "id": "5f126d84-551a-4dcf-bb01-0e9c0df0c793",
        "tenant_id": "8d4c70a21fed4aeba121a1a429ba0d04",
        "logging_resource_id": "46ebaec0-0570-43ac-82f6-60d2b03168c4",
        "description": "Collecting all traffic passing the firewall",
        "fw_event": "ALL",
        "firewall_id": "21aeda2a-a52f-4e81-9e64-7edeb59fa25b"
        }
    }

REST API Impact
---------------

The new resources::

    LOGGING_PREFIX = '/logging'
    FW_EVENT_ACCEPT = 'ACCEPT'
    FW_EVENT_DROP = 'DROP'
    FW_EVENT_ALL = 'ALL'
    FW_EVENTS = [FW_EVENT_ACCEPT, FW_EVENT_DROP, FW_EVENT_ALL]
    LOG_COMMON_FIELDS = {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True, 'primary_key': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True, 'is_visible': True},
        'logging_resource_id': {'allow_post': False, 'allow_put': False,
                                'is_visible': True}
    }

    RESOURCE_ATTRIBUTE_MAP = {
        'logging_resources': {
            'id': {'allow_post': False, 'allow_put': False,
                   'validate': {'type:uuid': None}, 'is_visible': True,
                   'primary_key': True},
            'tenant_id': {'allow_post': True, 'allow_put': False,
                          'required_by_policy': True, 'is_visible': True},
            'name': {'allow_post': True, 'allow_put': True,
                     'validate': {'type:string': attr.NAME_MAX_LEN},
                     'default': '', 'is_visible': True},
            'description': {'allow_post': True, 'allow_put': True,
                            'validate': {'type:string': attr.LONG_DESCRIPTION_MAX_LEN},
                            'default': '', 'is_visible': True},
            'enabled': {'allow_post': True, 'allow_put': True,
                        'is_visible': True, 'default': False,
                        'convert_to': attr.convert_to_boolean},
            'firewall_logs': {'allow_post': False, 'allow_put': False,
                              'is_visible': True}
        }
    }

    SUB_RESOURCE_ATTRIBUTE_MAP = {
        'firewall_logs': {
            'parent': {'collection_name': 'logging_resources',
                       'member_name': 'logging_resource'},
            'parameters': dict((LOG_COMMON_FIELDS),
                          **{
                            'description': {
                                'allow_post': True, 'allow_put': True,
                                'validate': {'type:string': None},
                                'default': None, 'is_visible': True},
                            'firewall_id': {
                                'allow_post': True, 'allow_put': False,
                                'is_visible': True,
                                'validate': {'type:uuid': None}},
                            'fw_event': {
                                'allow_post': True, 'allow_put': True,
                                'is_visible': True,
                                'validate': {'type:values': FW_EVENT},
                                'default': 'ALL'}
                          })
        },
    }

Logging format
--------------

Following items can be shown as follows.
Eventually, we catch up neutron behavior that agent collects logs and
sends logs to specified location from user.
Therefore, outputted items should be unified with neutron after supporting
function in neutron.

+-------------------+-------------------------------------------------------------+
|Item               |Description                                                  |
+===================+=============================================================+
|tenant_id          |Tenant ID of targeted firewall                               |
+-------------------+-------------------------------------------------------------+
|timestamp          |Time of the event is happened                                |
|                   |The time is based on ISO8601, time zone is UTC               |
+-------------------+-------------------------------------------------------------+
|firewall UUID      |UUID of neutron firewall                                     |
+-------------------+-------------------------------------------------------------+
|firewall rule UUID |UUID of neutron firewall rule                                |
+-------------------+-------------------------------------------------------------+
|router UUID        |UUID of neutron router                                       |
+-------------------+-------------------------------------------------------------+
|source IP address  |Source IP address of the communication                       |
+-------------------+-------------------------------------------------------------+
|destination IP     |Destination IP address of the communication                  |
|address            |                                                             |
+-------------------+-------------------------------------------------------------+
|source L4 port     |Source L4 port of the communication                          |
+-------------------+-------------------------------------------------------------+
|destination L4 port|Destination L4 port of the communication                     |
+-------------------+-------------------------------------------------------------+
|protocol           |IANA protocol number                                         |
+-------------------+-------------------------------------------------------------+
|action             |ACCEPT/DROP                                                  |
+-------------------+-------------------------------------------------------------+

Logging out location
--------------------

Currently, operators can only access directly to file on host that
midolman is running to consume log-data.
File location has format: /var/log/midolman/logging/fw-<firewall-log-uuid>.log
How generated log files are sent to tenants is up to the operator.
Backend implementation and/or log collector are expected to handle log rotation.
In the case with MidoNet, log rotation policy can be configured using its configuration tool.

DB Model impact
---------------

To avoid competition of table name with upstream,
we add specific initial to head of table names.
Note that upstream DB will be reused in newton or later
and DB in networking-midonet will be deleted.

The LoggingResource model has the following attributes:

**midonet_logging_resources**

+------------+-------+--------+----------+-----------+----------------------------+
|Attribute   |Type   |Access  |Default   |Validation/|Description                 |
|Name        |       |        |Value     |Conversion |                            |
+============+=======+========+==========+===========+============================+
|id          |uuid   |RO      |generated |uuid       |Identity                    |
+------------+-------+--------+----------+-----------+----------------------------+
|tenant_id   |uuid   |RO      |N/A       |uuid       |Id of tenant that created   |
|            |       |        |          |           |this LoggingResource        |
+------------+-------+--------+----------+-----------+----------------------------+
|name        |string |RW      |N/A       |none       |LoggingResource name        |
+------------+-------+--------+----------+-----------+----------------------------+
|description |string |RW      |N/A       |none       |LoggingResource description |
+------------+-------+--------+----------+-----------+----------------------------+
|enabled     |bool   |RW      |False     |Boolean    |Enable/disable log          |
+------------+-------+--------+----------+-----------+----------------------------+

The FirewallLog model would look like:

**midonet_firewall_logs**

+-------------------+-------+-------+---------+-----------+-----------------------+
|Attribute          |Type   |Access |Default  |Validation/|Description            |
|Name               |       |       |Value    |Conversion |                       |
+===================+=======+=======+=========+===========+=======================+
|id                 |uuid   |RO     |generated|uuid       |Identity               |
+-------------------+-------+-------+---------+-----------+-----------------------+
|logging_resource_id|uuid   |RO     |N/A      |uuid       |LoggingResource UUID   |
+-------------------+-------+-------+---------+-----------+-----------------------+
|tenant_id          |uuid   |RO     |generated|uuid       |Tenant creates logging |
+-------------------+-------+-------+---------+-----------+-----------------------+
|description        |string |RW     |N/A      |none       |FirewallLogging        |
|                   |       |       |         |           |description            |
+-------------------+-------+-------+---------+-----------+-----------------------+
|fw_event           |enum   |RW     |N/A      |enum       |ACCEPT/DROP & ALL      |
|                   |       |       |         |           |(collect all           |
|                   |       |       |         |           |ACCEPT/DROP events)    |
+-------------------+-------+-------+---------+-----------+-----------------------+
|firewall_id        |uuid   |RW(No  |N/A      |uuid       |Firewalls UUID         |
|                   |       |update)|         |           |is enabled logging     |
+-------------------+-------+-------+---------+-----------+-----------------------+

Quota
-----

Firewall log is managed by Quota.
Default value of firewall log is 10 that is same number as firewall.
Basically, both Quota value for firewall and firewall log should be aligned.

CLI Impact
----------

Additional methods will be added to python-neutronclient to create, update,
delete, list, get logging resource and firewall logging.

Checking support resource logging

For logging resource::

    neutron logging-create --name <logging-resource-name>
                           [--enable <True/False>]
                           [--description <logging-resource-description>]
    neutron logging-list
    neutron logging-update <logging-resource-name-or-id>
                           [--name ...]
                           [--description ...]
                           [--enable <True/False>]
    neutron logging-show <logging-resource-name-or-id>
    neutron logging-delete <logging-resource-name-or-id>

For firewalls logging::

    neutron logging-firewall-create <logging-resource-name-or-id> <firewall-id>
                                    [--description <firewall-log description>]
                                    [--fw-event <ACCEPT/DROP/ALL>]
    neutron logging-firewall-list <logging-resource-name-or-id>
    neutron logging-firewall-update <logging-resource-name-or-id> <firewall-log-id>
                                    [--description ...]
                                    [--fw-event ...]
    neutron logging-firewall-show <logging-resource-name-or-id> <firewall-log-id>
    neutron logging-firewall-delete <logging-resource-name-or-id> <firewall-log-id>


Other Deployer Impact
---------------------

Set quota for firewall log in quotas section of neutron.conf.

quota_firewall_log = 10


References
==========
.. [1] http://docs-draft.openstack.org/09/203509/41/check/gate-neutron-specs-docs/34a11fa//doc/build/html/specs/newton/logging-API-for-security-group-rules.html
.. [2] https://github.com/openstack/neutron-specs/blob/master/specs/newton/fwaas-api-2.0.rst
