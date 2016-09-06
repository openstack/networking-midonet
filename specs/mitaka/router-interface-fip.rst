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
This extension allows to associate floating-ip-B to fixed-ip-X.

* floating-ip-A is created on network4.

* floating-ip-B is created on network3.

* Both of floating-ip-A and floating-ip-B are associated to fixed-ip-X.

* fixed-ip-Y and fixed-ip-Z don't have any floating ip associations.

::

    +-----------------------+
    |  network4             |
    |  (external=True)      |
    +------------------+----+
                       |
                       |
                       |router gateway port
                       |(its primary address is gw-ip)
             +---------+--------------------------------------------+
             |      floating-ip-A                                   |
             |                                                      |
             |    router                                            |
             |    (enable_snat=True)                                |
             |                                                      |
             |                                        floating-ip-B |
             +----+-----------------+--------------------+----------+
                  |router           |router              |router
                  |interface        |interface           |interface
                  |                 |                    |
                  |                 |                    |
      +-----------+-----+    +------+----------+    +----+------------+
      | network1        |    | network2        |    | network3        |
      | (external=False)|    | (external=False)|    | (external=True) |
      +-----+-----------+    +--------+--------+    +------+----------+
            |                         |                    |
        +---+-------+             +---+-------+        +---+-------+
        |fixed-ip-X |             |fixed-ip-Y |        |fixed-ip-Z |
        +-----------+             +-----------+        +-----------+
           VM-X                      VM-Y                 VM-Z


In case multiple floating ip addresses are associated to a fixed ip address,
a datapath should be careful which floating ip to use for SNAT:

* If there's a floating ip associated via the egress port, either the
  router gateway port or a router interface, it should be used.
  For example, in the case of the above diagram, if VM-X sends a packet
  "fixed-ip-X -> fixed-ip-Z", floating-ip-B, rather than floating-ip-A,
  should be used.

* Otherwise, if there's a floating ip associated via the router gateway
  port, it should be used.  For example, in the case of the above diagram,
  if VM-X sends "fixed-ip-X -> fixed-ip-Y", floating-ip-A should be used.

* Otherwise, the datapath can choose arbitrary one.

A few interesting cases:

* If VM-Y sends a packet "fixed-ip-Y -> floating-ip-A", it's translated to
  "gw-ip -> fixed-ip-X" by the router and VM-X will receive it.
  This behaviour is not specific to this extension.  See bug 1428887
  [#bug_1428887]_ for the reason of the SNAT.

* If VM-Y sends a packet "fixed-ip-Y -> floating-ip-B", it's translated to
  "gw-ip -> fixed-ip-X" by the router and VM-X will receive it.
  However, its return traffic "fixed-ip-X -> gw-ip" will be translated to
  "floating-ip-A -> fixed-ip-Y" and probably will not be recognized as
  a return traffic by VM-Z's network stack.

* If VM-Z sends a packet "fixed-ip-Z -> floating-ip-B", it's translated to
  "fixed-ip-Z -> fixed-ip-X" by the router and VM-X will receive it.
  While this case is very similar to the above cases, the SNAT should not
  be applied here.  The datapath can distinguish these cases by the existance
  of the asssociation of a floating-ip via the router interface. (floating-ip-B)
  This behaviour is necessary for the primary use case. [#manila_neutron_integration]_

* If VM-Z sends a packet "fixed-ip-Z -> floating-ip-A", it's translated to
  "fixed-ip-Z -> fixed-ip-X" by the router and VM-X will receive it.
  However, its return traffic "fixed-ip-X -> fixed-ip-Z" will be translated to
  "floating-ip-B -> fixed-ip-Z" and probably will not be recognized as
  a return traffic by VM-Z's network stack.

API changes
~~~~~~~~~~~

For API, at least following changes are necessary:

* Add an extension "router-interface-fip" for feature discovery.
  The extension does not add any resources or attributes to the REST API.

* Allow floating IP association via a router interface.

* The existing RouterExternalGatewayInUseByFloatingIp check needs to be
  tweaked so that it doesn't count floating IPs associated via router
  interfaces.

* A check similar to RouterExternalGatewayInUseByFloatingIp but for
  router interfaces needs to be introduced.

Datapath support
~~~~~~~~~~~~~~~~

The datapath needs to be updated to perform actual address translations.

In case of MidoNet, latest versions have the basic support already. [#midonet_backend_change]_

The following is an example of a pseudo rules for logical router's
PREROUTING/POSTROUTING processing::

    PREROUTING

        // floating ip dnat
        [per FIP]
        (dst) matches (fip) -> float dnat, ACCEPT

        // rev-snat for the default snat
        [if default SNAT is enabled on the router]
        (dst) matches (gw port ip) -> rev-snat, ACCEPT

        // rev-snat for MidoNet-specific "same subnet" rules
        [per RIF]
        (inport, dst) matches (rif, rif ip) -> rev-snat, ACCEPT

    POSTROUTING

        // floating ip snat
        // multiple rules in order to implement priority (which FIP to use)
        // Note: "fip port" below is a router port, either the router gateway
        // port or router interface, which owns the corresponding FIP
        // configured.
        [per FIP]
        (outport, src) matches (fip port, fip) -> float snat, ACCEPT

        ----- ordering barrier

        [per FIP]
        (src) matches (fip) -> float snat, ACCEPT  // gateway port

        ----- ordering barrier

        [per FIP]
        (src) matches (fip) -> float snat, ACCEPT  // non gateway port

        ----- ordering barrier

        // do not apply default snat if it came from external-like network
        // (router interfaces with FIPs, and the gateway port)
        // Note: iptables based implementations need to "emulate" inport
        // match (eg. using marks in PREROUTING) as it isn't available
        // in POSTROUTING.
        [per FIP port]
        (inport) matches (fip port) -> ACCEPT
        [if default SNAT is enabled on the router]
        inport == the gateway port -> ACCEPT

        ----- ordering barrier

        // apply the default snat for the gateway port
        [if default SNAT is enabled on the router]
        outport == the gateway port -> default snat, ACCEPT

        // for non-float -> float traffic  (cf. bug 1428887)
        // "dst-rewritten" condition here means float dnat was applied in
        // prerouting.  in case of iptables based implementations,
        // "--ctstate DNAT" might be used.
        [if default SNAT is enabled on the router]
        dst-rewritten -> default snat, ACCEPT

        // MidoNet-specific "same subnet" rules
        [per RIF]
        (inport == outport == rif) && dst != 169.254.169.254
            -> snat to rif ip, ACCEPT

        // non-float -> non-float in tenant traffic would come here


References
==========

.. [#manila_neutron_integration] https://docs.google.com/presentation/d/1-v-bCsaEphyS5HDnhUeI1KM5OssY-8P4WMpQZsOqSOA/edit#slide=id.g1232f85657_0_63
.. [#midonet_backend_change] https://review.gerrithub.io/#/q/I37d22d43e4bf95bcce870679083aa3e129de8ea7
.. [#bug_1428887] https://bugs.launchpad.net/neutron/+bug/1428887
