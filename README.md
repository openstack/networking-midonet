python-neutron-plugin-midonet
=============================

This is the downstream Midonet Neutron plugin.

To generate deb and rpm packages:

```
./package.sh <version>
```

In neutron.conf, set the core_plugin to:

```
core_plugin = midonet.neutron.plugin.MidonetPluginV2
```
