Rally plugins
=============

All \*.py modules from this directory will be auto-loaded by Rally and all
plugins will be discoverable. There is no need of any extra configuration
and there is no difference between writing them here and in rally code base.

Note that it is better to push all interesting and useful benchmarks to Rally
code base, this simplifies administration for Operators.

Rally Network Plugin
====================

This plugin adds create only tasks in Neutron as the default Rally code base
benchmarks allow create_delete/list/update operations only.

Set the following variables in networking-midonet.yaml to override the
defaults.::

    {% set rps_scalability = 0 %}
    {% set times_scalability = 0 %}
    {% set sla_scalability = 0 %}

MidoNet Rally Plugin
====================

This plugin allows to create MidoNet resources using the MidoNet REST
API directly so that the benchmarks can be compared with the resources created
using Neutron.
