
======================================
Networking-MidoNet Configuration Guide
======================================

This section provides a list of all possible options for each
configuration file.

Configuration
-------------

Networking-midonet uses the following configuration options
in the Neutron server configuration, which is typically
`/etc/neutron/neutron.conf`.

.. show-options::

    midonet_v2

Policy
------

Networking-MidoNet, like most OpenStack projects, uses a policy language to restrict
permissions on REST API actions.

.. toctree::
   :maxdepth: 1

   Policy Reference <policy>
   Sample Policy File <policy-sample>
