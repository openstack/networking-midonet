==================
Supported features
==================

Neutron extensions supported by MidoNet
---------------------------------------

MidoNet provides the following Neutron API extensions.
(The list doesn't include extensions implemented by Neutron in
a mostly backend-agnostic way, like ``subnet_allocation`` and
``standard-attr-revisions``.)

+-----------+------------------------------+----------------------------+
| Category  | Extension Alias              | Required MidoNet version   |
+===========+==============================+============================+
| Core      | extra_dhcp_opt               | >=5.2.1                    |
|           +------------------------------+----------------------------+
|           | port-security                | >=5.0                      |
|           +------------------------------+----------------------------+
|           | allowed-address-pairs        | >=5.0                      |
|           +------------------------------+----------------------------+
|           | external-net                 | >=5.0                      |
|           +------------------------------+----------------------------+
|           | provider                     | >=5.0                      |
|           +------------------------------+----------------------------+
|           | security-group               | >=5.0                      |
+-----------+------------------------------+----------------------------+
| L3        | router                       | >=5.0                      |
|           +------------------------------+----------------------------+
|           | extraroute                   | >=5.0                      |
|           +------------------------------+----------------------------+
|           | ext-gw-mode                  | >=5.0                      |
|           +------------------------------+----------------------------+
|           | router-interface-fip         | >=5.1.1                    |
|           +------------------------------+----------------------------+
|           | fip64                        | >=5.4                      |
+-----------+------------------------------+----------------------------+
| QoS       | qos                          | >=5.4                      |
+-----------+------------------------------+----------------------------+
| L2Gateway | gateway-device               | >=5.1                      |
|           +------------------------------+----------------------------+
|           | l2-gateway                   | >=5.1                      |
|           +------------------------------+----------------------------+
|           | l2-gateway-connection        | >=5.1                      |
+-----------+------------------------------+----------------------------+
| BGP       | bgp                          | >=5.2                      |
|           +------------------------------+----------------------------+
|           | bgp-speaker-router-insertion | >=5.2                      |
+-----------+------------------------------+----------------------------+
| Logging   | logging-resource             | >=5.2                      |
+-----------+------------------------------+----------------------------+
| TaaS      | taas                         | >=5.2                      |
+-----------+------------------------------+----------------------------+
| VPNaaS    | vpnaas                       | >=5.1                      |
|           +------------------------------+----------------------------+
|           | vpn-endpoint-groups          | >=5.1                      |
+-----------+------------------------------+----------------------------+
| LBaaS     | lbaasv2                      | >=5.4                      |
|           +------------------------------+----------------------------+
|           | shared_pools                 | >=5.4                      |
+-----------+------------------------------+----------------------------+
| FWaaS     | fwaas                        | >=5.0                      |
|           +------------------------------+----------------------------+
|           | fwaasrouterinsertion         | >=5.0                      |
+-----------+------------------------------+----------------------------+


FAQ
---

- MidoNet doesn't support IPv6 in general.  An exception is the ``fip64``
  extension.

- While the IPAM part of Neutron ``address-scope`` extension does work with
  networking-midonet, the routing decision part of it is not implemented.

- MidoNet doesn't support Neutron ``dvr`` extension because L3 routing is
  always distributed in MidoNet.

- MidoNet doesn't support Neutron ``l3-ha`` extension.  In MidoNet,
  It's common to use multiple router ports with BGP to provide a redundancy.
  [#config_uplink]_


.. [#config_uplink] https://docs.midonet.org/docs/latest-en/operations-guide/content/configuring_uplinks.html
