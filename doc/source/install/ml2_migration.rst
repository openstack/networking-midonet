=================================================
Migration from monolithic v2 plugin to ML2 plugin
=================================================


Overview
--------

MidoNet monolithic v2 plugin (`midonet_v2`) is not supported anymore.
When upgrading to Pike, a deployer needs to switch to ML2 with
MidoNet mechanism driver.  This document outlines the migration procedure.

.. note:: The procedure documented here is appropriate only when upgrading to Pike.


How to migrate
--------------

0. Take a backup. (not strictly necessary but strongly recommended)

1. Upgrade to Pike as usual.

   This step includes the usual DB migration via neutron-db-manage.

2. Update neutron configuration to use ML2 plugin.

   See the following section for examples.

3. Start neutron server.

   On the first startup, MidoNet mechanism driver automatically migrates
   the data in the Neutron DB from the form what MidoNet monolithic
   plugin recognises.  This is a one-way migration.  On successful
   migration, the message "DB Migration from MidoNet v2 to ML2
   completed successfully" will be logged in the neutron server log
   at `INFO` level.

.. note:: The Step 3 assumes it's the only neutron server process using the Neutron DB.  If your deployment has multiple neutron servers, make sure to shut them down prior to Step 3. After verifying that the migration succeeded, you can start them. Also, make sure that they are also configured to use ML2 and midonet mechanism driver.


Neutron server configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Basically, you need to:

- Change `core_plugin` to `ml2`

- Add the `ml2` group.

The :oslo.config:group:`midonet` group is common for both of
the monolithic plugin and the ML2 driver.
It doesn't need any changes.


Example before migration
........................

.. literalinclude:: samples/midonet.ini


Example after migration
.......................

.. literalinclude:: samples/ml2_midonet.ini
