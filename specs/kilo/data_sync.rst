..
 This work is licensed under a Creative Commons Attribution 4.0 International
 License.

 http://creativecommons.org/licenses/by/4.0/


=========
Data Sync
=========

In MidoNet 2.0, Neutron is the data store of network configurations and Cluster
is the backend data store that contains MidoNet-specific data objects
translated from Neutron data models.

Also, MidoNet 2.0 includes data syncing feature between Neutron and Cluster,
which is internally implemented by importing the Neutron data into Cluster
through the tasks table.  The data sync feature is needed for the following use
cases:

 * Operator sets up MidoNet for the first time and wants to initialize the
   Cluster data
 * Operator using a non-MidoNet Neutron plugin wishes to migrate over to
   MidoNet
 * Operator wants to upgrade to the new version of MidoNet and the MidoNet data
   schema has changed.
 * Modifying either the Neutron DB or MidoNet data store directly for some
   operational purpose led to severe data mismatch between Neutron and MidoNet,
   and wishes to re-sync.

Each data imported is versioned.  This document describes the data version
management feature of midonet-db-manage tool that includes syncing Neutron and
Cluster data, and rolling back to one of the previous data versions.

The Cluster design of data import, and the upgrade process, are outside the
scope of this document.


Problem Description
===================

While MidoNet 2.0 is designed to provide the data syncing feature, currently
there is no tool made available in Neutron to facilitate it.  Without such a
tool, the data sync feature does not get exposed to the operators, making the
upgrade process and data re-syncing between Neutron and MidoNet challenging.


Proposed Change
===============

midonet-db-manage, which manages the tasks table in Neutron DB among other DB
related features, is enhanced with the following capabilities:

 * Toggle the write access of the tasks table between read-only and read-write
   modes, which also toggles the API between read-only and read-write
   correspondingly
 * Through the tasks table, signal to Cluster that data sync is about to start
   and execute the data import, and signal that the import has completed to
   activate the imported data
 * Maintain all the past data sync events and their summaries

Deletion of the imported Cluster data is not included in this proposal, but it
is planned to be included in one of the future releases.


Tasks Write Access
------------------

A new column is added to 'midonet_data_state' table which indicates the write
access to the tasks table.  The default is read-write.  The data sync operation
is only allowed in the read-only mode, and the operator cannot switch back to
read-write while the data sync is taking place.  The plugin will throw 503
(Service Unavailable) on all the POST/PUT/DELETE Neutron API requests if the
tasks table is in a read-only mode.


Data Version
------------

Each data sync event is summarized and saved in the 'midonet_data_versions'
table as a new 'data version'.  A data version includes fields that are updated
only by midonet-db-manage and fields updated only by Cluster.

The fields updated by midonet-db-manage are:

 * id: Globally unique identifier of the data version
 * sync_started_at: Time the sync started
 * sync_tasks_status: Status of sync tasks insertion
 * stale: Flag indicating that this data set is out of date

The field updated by Cluster is

 * sync_finished_at: Time all the tasks were processed by Cluster

Both midonet-db-manage and Cluster update:

 * sync_status: Status of the sync.  midonet_db_manager updates it when it starts,
                and Cluster updates when it finishes processing all the tasks

How these fields get set are described in Tasks Data Sync section below.

The data version summary does not include the number of tasks processed but
such information would be printed and logged from the midonet-db-manage
command, and may be added to the table if there are clear use cases for it.

When the midonet-db-manage sync command is issued, 'id', 'sync_started_at' and
'sync_tasks_status' are initialized.  'sync_tasks_status' is set to STARTED.

When the midonet-db-manage finishes adding all the tasks, 'sync_tasks_status'
is updated to COMPLETED.


Tasks Data Sync
---------------

The data sync operation is allowed only when the data write access is set to
read-only.

The data sync operation is implemented as follows:

 1. midonet-db-manage truncates the tasks table and inserts a DATA_VERSION_SYNC
    task in the first row.  This task instructs Cluster that a new data sync
    has started, and it needs to prepare a new storage for the sync.
    midonet-db-manage sets 'sync_started_at' to the current time, and
    'sync_tasks_status' and 'sync_status' to STARTED.  Syncing is disallowed in
    the following cases:

        a. Sync is already being executed
        b. There are unprocessed tasks (so that truncate does not delete
           unprocessed tasks)

 2. Immediately following the DATA_VERSION_SYNC task insertion,
    midonet-db-manage queries Neutron DB and generates CREATE tasks for all the
    existing resources.  Cluster processes them as usual and creates these
    resources in the backend.
 3. Once all the tasks to re-create the Neutron objects are inserted into the
    tasks table, DATA_VERSION_ACTIVATE task is added to indicate that the import
    has finished. midonet-db-manage updates the 'sync_task_status' to COMPLETED

midonet-db-manage sync command exits immediately after DATA_VERSION_ACTIVE task
has been added to the tasks table, and does not know whether Cluster has
successfully processed all the tasks.  'sync_status' and 'sync_tasks_status'
exist to differentiate the statuses of the Cluster processing and the
midonet-db-manage command.

Cluster, after processing DATA_VERSION_ACTIVATE task, updates 'sync_status' to
COMPLETED.  If Cluster encounters an error, it updates 'sync_status' to ERROR.
In both cases, 'sync_finished_at' is updated.

If there was an error while inserting sync tasks, midonet-db-manager updates
'sync_tasks_status' to ERROR.  If the sync command was forcefully terminated
(SIGINT) by the user, then 'sync_tasks_status' is set to ABORTED.  In both
cases, the command terminates immediately, and adds DATA_VERSION_ACTIVE task
with the version ID set to the currently active data version (not the one being
synced).


Data Version Activation
-----------------------

An active data version means that the data originated from this data sync event
is what the MidoNet agents are currently using for packet simulation.  At any
time, exactly one data version may be active.  When a data sync process
completes, the newly imported data set is automatically activated.

In addition, midonet-db-manage offers a command to rollback to the previously
active data version.  A rollback could only happen during one read-only
session.  Once the operator sets the API to read-write, none of the previously
synced data could be chosen for a rollback.  You can only rollback to the data
sync that was completed in the same read-only session.  The operator is
expected to do all the necessary verifications of the completed data sync
before the data access is set back to read-write.  When the data is set back to
read-write, midonet-db-manage sets the 'stale' field of all the non-active data
versions to true.

When a data activation command is issued, midonet-db-manage sets the
'sync_status' and 'task_status' to STARTED.  When the command completes, it
sets the 'task_status' to COMPLETED.  Cluster, when it finishes the activation
process, updates 'sync_status' to COMPLETED, and 'active_data_version' field of
the midonet-data-state table to the activated version.

You can not go back to the read-write mode if either 'task_status' or
'sync_status' field is set to STARTED.


REST API
--------

None


DB Model
--------

**midonet_data_versions**

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| id                | Int     | The version of the data                       |
+-------------------+---------+-----------------------------------------------+
| sync_started_at   | DateTime| Time the data sync started                    |
+-------------------+---------+-----------------------------------------------+
| sync_finished_at  | DateTime| Time the data sync finished                   |
+-------------------+---------+-----------------------------------------------+
| sync_status       | String  | Status of the sync operation                  |
+-------------------+---------+-----------------------------------------------+
| sync_tasks_status | String  | Status of the sync tasks insertion            |
+-------------------+---------+-----------------------------------------------+
| stale             | Boolean | True if the date version is stale             |
+-------------------+---------+-----------------------------------------------+

The 'sync_status' column could contain one of the following values:

 * STARTED
 * COMPLETED
 * ERROR

The 'sync_tasks_status' column could contain one of the following values:

 * STARTED
 * COMPLETED
 * ABORTED
 * ERROR


**midonet_data_state**

Rename midonet_task_state to midonet_data_state.

Add a new column to store the write access to the tasks table.

+-------------------+---------+-----------------------------------------------+
| Name              | Type    | Description                                   |
+===================+=========+===============================================+
| active_version    | Int     | Active data version                           |
+-------------------+---------+-----------------------------------------------+
| readonly          | Boolean | If true, tasks table is readonly              |
+-------------------+---------+-----------------------------------------------+

FLUSH task type is deleted, and new resource types, DATA_VERSION_SYNC and
DATA_VERSION_ACTIVATE are created.

To start the data sync process, this is added in row 1 of the tasks table:

::
    task_type: DATA_VERSION_SYNC
    resource_type:
    resource_id: <DATA_VERSION>
    data: {}

To activate a data version, this is added to the tasks table:

::
    task_type: DATA_VERSION_ACTIVATE
    resource_type:
    resource_id: <DATA_VERSION>
    data: {}


Security
--------

Similar to neutron-db-manage, only the admins are expected to run
midonet-db-manage.  While there is no special authentication mechanism
implemented for this tool, the only way to run this script is if you have
access to the management hosts in the cloud, and preventing unauthorized users
from gaining such access is out of this document's scope.


Client
------

The following command displays the global information about the data, including
the write access and the last processed task:

::
    midonet-db-manage data-show


The following command sets the Neutron data to be read-only:

::
    midonet-db-manage data-readonly


The following command sets the Neutron data to be read-write:

::
    midonet-db-manage data-readwrite


The following command displays all the data versions:

::
    midonet-db-manage data-version-list


The following command starts data sync to create a new version:

::
    midonet-db-manage data-version-sync


The following command activates the specified version.  It could be used for
the rollback:

::
    midonet-db-manage data-version-activate <VERSION_ID>


Documentation
-------------

In the Deployment Guide, the following section is added:

 * How to initialize the Cluster data when Setting up MidoNet for the first
   time
 * How to initialize the Cluster data when migration from a different Neutron
   plugin
 * Within the upgrade section, how to sync the data from Neutron to Cluster,
   including how the rollback is accomplished

In the Operational Guide, the following section is added:

 * How to sync data between Neutron and Cluster when the data between them
   become inconsistent due to some operational errors

