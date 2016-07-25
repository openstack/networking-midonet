..
 This work is licensed under a Creative Commons Attribution 3.0 Unported
 License.

 http://creativecommons.org/licenses/by/3.0/legalcode

=================================
Floating IP via router interfaces
=================================

This spec describes an extension to associate floating IPs via router
interfaces, rather than the router gateway port.


Problem Description
===================

For some use cases [#manila_neutron_integration]_, it can be useful
to make floating IP translation happens on non-gateway router interfaces.


Proposed Change
===============

Introduce "router-interface-fip" extension, which allows users to
associate floating IPs via router interfaces.

Consider the topology like the following diagram.
Allow to associate a floating IP allocated on the "external network2" to
a fixed IP on "private network".

::

    +-----------------------+
    |  external             |
    |  network1             |
    |                       |
    |                       |
    |        floating-ip    |
    +------------------+----+
                       |
                       |
                       |router gateway port
             +---------+-----------------------------------+
             |                                             |
             |    router                                   |
             |                                             |
             +----+---------------------------+------------+
                  |router                     |router
                  |interface                  |interface
                  |                           |
                  |                           |
    +-------------+-------+       +-----------+----------+
    |   private           |       |   external           |
    |   network           |       |   network2           |
    |                     |       |                      |
    |        fixed-ip     |       |        floating-ip   |
    +---------------------+       +----------------------+

For API, at least following changes are necessary:

* Add an extension "router-interface-fip" for feature discovery.
  The extension does not add any resources or attributes to the REST API.

* Allow floating IP association via a router interface.

* The existing RouterExternalGatewayInUseByFloatingIp check needs to be
  tweaked so that it doesn't count floating IPs associated via router
  interfaces.

* A check similar to RouterExternalGatewayInUseByFloatingIp but for
  router interfaces needs to be introduced.

The datapath needs to be updated to perform actual address translations.
In case of MidoNet, latest versions have the support already. [#midonet_backend_change]_


References
==========

.. [#manila_neutron_integration] https://docs.google.com/presentation/d/1-v-bCsaEphyS5HDnhUeI1KM5OssY-8P4WMpQZsOqSOA/edit#slide=id.g1232f85657_0_63
.. [#midonet_backend_change] https://review.gerrithub.io/#/q/I37d22d43e4bf95bcce870679083aa3e129de8ea7
