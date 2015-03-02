..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/


===============
Task Management
===============

Neutron and the MidoNet cluster, which is the distributed network configuration
storage service of MidoNet, communicate via the tasks database table.  A task
represents a single Neutron API operation that the cluster translates into
lower level MidoNet concepts.  This table stores as tasks all the API write
requests as well as Neutron's global configurations specified in neutron.conf
during the initialization stage.  They are processed by the cluster in the
order inserted.  This document describes new commands of midonet-db-manage tool
that provide tasks table management functionalities.


Problem Description
===================

While the tasks table provide a reliable communication channel between Neutron
and MidoNet, it lacks the following features:

 * Ability to view/filter the processed and unprocessed tasks for debugging
 * Ability to clean up the processed tasks.  You should be able to delete all
   the processed tasks.


Proposed Change
===============

New commands are added to midonet-db-manage tool to provide better visibility
into the tasks table as well as a way to safely clean up the processed tasks.
They do not belong in the Neutron API because they have very little to do with
network management.  Note that only the manual clean up of the tasks is
described in this proposal, and there will be a separate proposal to address
the automatic clean-up.

To implement the commands, the last processed task ID, which is currently
maintained by the cluster, needs to be also stored in the Neutron DB so that
midonet-db-manage could use this value to differentiate the processed and
unprocessed tasks.  The task IDs are auto-incremented integer field, and
the last processed task ID indicates the latest task that was processed by the
cluster.

The cluster processes a transaction consisting of one or more tasks atomically,
and in the same transaction, the ID of the last processed task is stored.  The
cluster then stores this task ID in Neutron DB's midonet_task_state table.  If
the Neutron DB update fails due to a temporary resource issue, such as network
disruption, the cluster will re-sync in the next successful task processing.
It is guaranteed that the last processed task ID in the cluster never trails
that of Neutron because the cluster always updates its last processed task ID
before it updates the Neutron DB's table.  This means that there may be tasks
that are not yet marked as processed by the cluster in the Neutron DB that have
actually already been processed.  However, the reverse cannot be true.

Once the last processed task ID is made available to Neutron, midonet-db-manage
could easily separate the processed and unprocessed tasks by querying the
tasks table filtered by this value.  While it may be useful to filter the tasks
based on other criteria, such as tenant ID, resource ID, and resource type, but
such feature will be addressed in a different proposal to not over-complicate.


REST API
--------

None


DB Model
--------

**midonet_task_state**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | Int     | The primary key useful to idenfity the single |
|                   |         | row (Set to 1)                                |
+-------------------+---------+-----------------------------------------------+
| last_processed_id | Int     | The last processed task ID (default NULL)     |
+-------------------+---------+-----------------------------------------------+
| updated_at        | DateTime| Time of the last update (default NULL)        |
+-------------------+---------+-----------------------------------------------+

midonet_task_state is a singe-row table representing the current state of the
tasks table.  It is created and data initialized by the alembic migration
script.  The single row is created during the alembic migration with default
values.  The cluster updates this table when it completes processing a
particular task.

'last_processed_id' has foreign key reference to the tasks table's 'id' column.

'id' is used by the cluster to identify the single row.  Also, sqlalchemy
requires that there is a primary key column.  The 'id' of the single row is set
to 1.


Security
--------

Similar to neutron-db-manage, only the admins are expected to run
midonet-db-manage.  While there is no special authentication mechanism
implemented for this tool, the only way to run this script is if you have
access to the management hosts in the cloud, and preventing unauthorized users
from gaining such access is out of this document's scope.


Client
------

The following command lists the tasks:

::
    midonet-db-manage task-list [-u]


-u, --unprocessed::
    Show only the processed tasks


The following command deletes the processed tasks:

::
    midonet-db-manage task-clean

When the processed tasks are deleted, the last_processed_id is reset to NULL.
Note that there is no command to delete unprocessed tasks because such command
is dangerous, and will be addressed separately when the upgrade/import feature
is designed.  If that must be done, then the operator must do so directly from
the sql client.

The following command displays the state of the resources based on the tasks so
that you can see which ones should (or will) exist.  This is implemented with
'best effort' since the tasks table may not contain the entire history:

::
    midonet-db-manage task-resource [-p]

-p, --processed::
    Calculate based on only the processed tasks
