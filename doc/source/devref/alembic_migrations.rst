Alembic Migrations
==================

Script Auto-generation
----------------------

Please refer to the Neutron documentation
`Script Auto-generation <http://docs.openstack.org/developer/neutron/devref/alembic_migrations.html#script-auto-generation>`_
for the instruction to auto-generate migration scripts.

You need to specify `--subproject networking-midonet` option to the
`neutron-db-manage` command to generate a migration script for this project.

Depending on \*aaS and other sub-projects set up in your environment,
you might need to edit the generated script.  Typically, you need to
remove extra "drop table" ops for tables which don't belong to our project.
