========================================================
Developer quick-start for MidoNet + Magnum with DevStack
========================================================

Resource requirement
--------------------

I (yamamoto) was able to run the following instruction on
an Ubuntu 14.04 VM with ~10GB memory and ~20GB disk.

Instructions
------------

1. Prepare `local.conf` by using an example within this directory as a base.
   You need to tweak some of settings for your environment, including::

        FIXED_RANGE
        NETWORK_GATEWAY
        FLOATING_RANGE
        various passwords

   Importantly, you need to provide Internet connectivity from VMs
   so that Magnum deployment can pull docker images etc.

   Note: The way Magnum uses Neutron LB for its deployment is incompatible
   with MidoNet native LB.  Namely, MidoNet native LB has the following
   limitations:

     * floating-ip association to VIPs is not supported
     * http is not supported
     * the tenant router needs to exist on pool creation time

   The `local.conf` example in this directory uses haproxy provider instead
   of MidoNet native LB to workaround the issue.

2. Run stack.sh

3. Create a keypair as described in Magnum documentation.
   [#magnum_quick_start1]_

4. Now you can create a bay, following Magnum documentation.
   [#magnum_quick_start2]_

   Note: There's a known issue [#magnum_quick_start_issue]_
   with the example.  It isn't specific to MidoNet.

   Note: I (yamamoto) only tested kubernetes with atomic.

5. You can setup certs, following the instruction found in the Magnum
   documentation [#magnum_tls], to connect to the kubernetes API in the bay.
   Magnum sets up VIP for the API::

     ubu8% neutron lb-vip-list
     +--------------------------------------+---------------+----------+----------+----------------+--------+
     | id                                   | name          | address  | protocol | admin_state_up | status |
     +--------------------------------------+---------------+----------+----------+----------------+--------+
     | 2a2f87c0-7735-4bb6-8bd6-c03949b4ab66 | api_pool.vip  | 10.0.0.3 | TCP      | True           | ACTIVE |
     | d19a8e5f-13e6-49a3-8a33-bb53b01628c4 | etcd_pool.vip | 10.0.0.2 | HTTP     | True           | ACTIVE |
     +--------------------------------------+---------------+----------+----------+----------------+--------+
     ubu8% neutron floatingip-list
     +--------------------------------------+------------------+---------------------+--------------------------------------+
     | id                                   | fixed_ip_address | floating_ip_address | port_id                              |
     +--------------------------------------+------------------+---------------------+--------------------------------------+
     | 299e5312-7258-45dd-9514-8fcda5091676 | 10.0.0.3         | 172.24.4.4          | eca69613-e5e7-4892-b901-fbc3bb98a3c7 |
     | d3c8ccd3-c938-4622-b820-7c71549ce05e | 10.0.0.4         | 172.24.4.5          | 12d57d5e-1244-440d-af8c-6ee4464027d7 |
     | f96e9387-6897-4fb2-902d-9af3348c9e1d | 10.0.0.5         | 172.24.4.6          | c696e16c-e0f9-4c56-94ab-3b161840de2b |
     +--------------------------------------+------------------+---------------------+--------------------------------------+
     ubu8% ./cluster/kubectl.sh --certificate-authority /tmp/cert/ca.crt --client-certificate /tmp/cert/client.crt --client-key /tmp/cert/client.key --server https://172.24.4.4:6443 get po
     NAME                 READY     STATUS    RESTARTS   AGE
     frontend-8ph1a       1/1       Running   0          2h
     frontend-bpmuw       1/1       Running   0          2h
     frontend-gko84       1/1       Running   0          2h
     redis-master-8nmcn   1/1       Running   0          2h
     redis-slave-0rv73    1/1       Running   0          2h
     redis-slave-3zy7n    1/1       Running   0          2h
     ubu8%

.. [#magnum_quick_start1] https://docs.openstack.org/magnum/latest/contributor/quickstart.html#exercising-the-services-using-devstack

.. [#magnum_quick_start2] https://docs.openstack.org/magnum/latest/contributor/quickstart.html#building-a-kubernetes-cluster-based-on-fedora-atomic

.. [#magnum_quick_start_issue] https://bugs.launchpad.net/magnum/+bug/1556001

.. [#magnum_tls] https://docs.openstack.org/magnum/latest/user/#transport-layer-security
