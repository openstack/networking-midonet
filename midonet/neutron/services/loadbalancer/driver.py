# Copyright (C) 2015 Midokura SARL
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from midonet.neutron.client import base as c_base
from midonet.neutron.db import loadbalancer_db as mn_lb_db

from neutron.common import exceptions as n_exc
from neutron import i18n
from neutron.plugins.common import constants
from neutron_lbaas.db.loadbalancer import loadbalancer_db as ldb
from neutron_lbaas.services.loadbalancer.drivers import abstract_driver

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import excutils

_LE = i18n._LE
LOG = logging.getLogger(__name__)


class MidonetLoadbalancerDriver(abstract_driver.LoadBalancerAbstractDriver,
                                mn_lb_db.LoadBalancerDriverDbMixin):

    def __init__(self, plugin):
        self.plugin = plugin
        self.client = c_base.load_client(cfg.CONF.MIDONET)

    @property
    def core_plugin(self):
        return self.plugin._core_plugin

    def create_vip(self, context, vip):
        LOG.debug("MidonetLoadbalancerDriver.create_vip called: %(vip)r",
                  {'vip': vip})

        try:
            self._validate_vip_subnet(context, vip)
        except n_exc.NeutronException as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a vip %(vip_id)s in Midonet: "
                              "%(err)s"), {"vip_id": vip["id"], "err": ex})
                try:
                    self.plugin._delete_db_vip(context, vip['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete vip %s"), vip['id'])

        self.client.create_vip(context, vip)
        self.plugin.update_status(context, ldb.Vip, vip['id'],
                                  constants.ACTIVE)

        LOG.debug("MidonetLoadbalancerDriver.create_vip exiting: id=%r",
                  vip['id'])

    def delete_vip(self, context, vip):
        LOG.debug("MidonetLoadbalancerDriver.delete_vip called: id=%(vip)r",
                  {'vip': vip})

        self.client.delete_vip(context, vip['id'])
        self.plugin._delete_db_vip(context, vip['id'])

        LOG.debug("MidonetLoadbalancerDriver.delete_vip existing: vip=%(vip)r",
                  {'vip': vip})

    def update_vip(self, context, old_vip, new_vip):
        LOG.debug("MidonetLoadbalancerDriver.update_vip called: "
                  "old_vip=%(old_vip)r, new_vip=%(new_vip)r",
                  {'old_vip': old_vip, 'new_vip': new_vip})

        try:
            self._validate_vip_subnet(context, new_vip)
        except n_exc.NeutronException as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to update a vip %(vip_id)s in Midonet: "
                              "%(err)s"), {"vip_id": old_vip["id"], "err": ex})
                try:
                    self.plugin.update_status(context, ldb.Vip, old_vip["id"],
                                              constants.ERROR)
                except Exception:
                    LOG.exception(_LE("Failed to update vip status %s"),
                                  old_vip['id'])

        self.client.update_vip(context, old_vip['id'], new_vip)
        self.plugin.update_status(context, ldb.Vip, old_vip["id"],
                                  constants.ACTIVE)

        LOG.debug("MidonetLoadbalancerDriver.update_vip exiting: "
                  "old_vip=%(old_vip)r, new_vip=%(new_vip)r",
                  {'old_vip': old_vip, 'new_vip': new_vip})

    def create_pool(self, context, pool):
        LOG.debug("MidonetLoadbalancerDriver.create_pool called: %(pool)r",
                  {'pool': pool})

        try:
            router_id = self._check_and_get_router_id_for_pool(
                context, pool['subnet_id'])
        except n_exc.NeutronException as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a pool %(pool_id)s in "
                              "Midonet: %(err)s"),
                          {"pool_id": pool["id"], "err": ex})
                try:
                    self.plugin._delete_db_pool(context, pool['id'])
                except Exception:
                    LOG.exception(_LE("Failed to delete pool %s"), pool['id'])

        pool.update({'router_id': router_id, 'status': constants.ACTIVE})
        self.client.create_pool(context, pool)
        self.plugin.update_status(context, ldb.Pool, pool['id'],
                                  constants.ACTIVE)

        LOG.debug("MidonetLoadbalancerDriver.create_pool exiting: %(pool)r",
                  {'pool': pool})

    def delete_pool(self, context, pool):
        LOG.debug("MidonetLoadbalancerDriver.delete_pool called: %(pool)r",
                  {'pool': pool})

        self.client.delete_pool(context, pool['id'])
        self.plugin._delete_db_pool(context, pool['id'])

        LOG.debug("MidonetLoadbalancerDriver.delete_pool exiting: %(pool)r",
                  {'pool': pool})

    def update_pool(self, context, old_pool, new_pool):
        LOG.debug("MidonetLoadbalancerDriver.update_pool called: "
                  "old_pool=%(old_pool)r, new_pool=%(new_pool)r",
                  {'old_pool': old_pool, 'new_pool': new_pool})

        self.client.update_pool(context, old_pool['id'], new_pool)
        self.plugin.update_status(context, ldb.Pool, old_pool["id"],
                                  constants.ACTIVE)

        LOG.debug("MidonetLoadbalancerDriver.update_pool exiting: "
                  "new_pool=%(new_pool)r", {'new_pool': new_pool})

    def create_member(self, context, member):
        LOG.debug("MidonetLoadbalancerDriver.create_member called: %(member)r",
                  {'member': member})

        self.client.create_member(context, member)
        self.plugin.update_status(context, ldb.Member, member['id'],
                                  constants.ACTIVE)

        LOG.debug("MidonetLoadbalancerDriver.create_member exiting: "
                  "%(member)r", {'member': member})

    def delete_member(self, context, member):
        LOG.debug("MidonetLoadbalancerDriver.delete_member called: %(member)r",
                  {'member': member})

        self.client.delete_member(context, member['id'])
        self.plugin._delete_db_member(context, member['id'])

        LOG.debug("MidonetLoadbalancerDriver.delete_member exiting: "
                  "%(member)r", {'member': member})

    def update_member(self, context, old_member, new_member):
        LOG.debug("MidonetLoadbalancerDriver.update_member called: "
                  "old_member=%(old_member)r, new_member=%(new_member)r",
                  {'old_member': old_member, 'new_member': new_member})

        self.client.update_member(context, old_member['id'], new_member)
        self.plugin.update_status(context, ldb.Member, old_member["id"],
                                  constants.ACTIVE)

        LOG.debug("MidonetLoadbalancerDriver.update_member exiting: "
                  "new_member=%(new_member)r", {'new_member': new_member})

    def create_pool_health_monitor(self, context, health_monitor, pool_id):
        LOG.debug("MidonetLoadbalancerDriver.create_pool_health_monitor "
                  "called: hm=%(health_monitor)r, pool_id=%(pool_id)r",
                  {'health_monitor': health_monitor, 'pool_id': pool_id})

        try:
            self._validate_pool_hm_assoc(context, pool_id,
                                         health_monitor['id'])
        except n_exc.NeutronException as ex:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Failed to create a pool-hm association "
                              "in Midonet: pool=%(pool_id)s, hm=%(hm_id)s, "
                              "%(err)s"),
                          {"pool_id": pool_id, "hm_id": health_monitor['id'],
                           "err": ex})
                try:
                    self.plugin._delete_db_pool_health_monitor(
                        context, health_monitor['id'], pool_id)
                except Exception:
                    LOG.exception(_LE("Failed to delete pool-hm association:"
                                      "pool_id=%(pool_id)s, hm_id=%(hm_id)s"),
                                  {"pool_id": pool_id,
                                   "hm_id": health_monitor['id']})

        self.client.create_health_monitor(context, health_monitor)
        self.plugin.update_pool_health_monitor(context, health_monitor['id'],
                                               pool_id, constants.ACTIVE, "")

        LOG.debug("MidonetLoadbalancerDriver.create_pool_health_monitor "
                  "exiting: %(health_monitor)r, %(pool_id)r",
                  {'health_monitor': health_monitor, 'pool_id': pool_id})

    def delete_pool_health_monitor(self, context, health_monitor, pool_id):
        LOG.debug("MidonetLoadbalancerDriver.delete_pool_health_monitor "
                  "called: health_monitor=%(health_monitor)r, "
                  "pool_id=%(pool_id)r", {'health_monitor': health_monitor,
                                          'pool_id': pool_id})

        self.client.delete_health_monitor(context, health_monitor['id'])
        self.plugin._delete_db_pool_health_monitor(context,
                                                   health_monitor['id'],
                                                   pool_id)

        LOG.debug("MidonetLoadbalancerDriver.delete_pool_health_monitor "
                  "exiting: %(health_monitor)r, %(pool_id)r",
                  {'health_monitor': health_monitor, 'pool_id': pool_id})

    def update_pool_health_monitor(self, context, old_health_monitor,
                                   health_monitor, pool_id):
        LOG.debug("MidonetLoadbalancerDriver.update_pool_health_monitor "
                  "called: old_health_monitor=%(old_health_monitor)r, "
                  "health_monitor=%(health_monitor)r, pool_id=%(pool_id)r",
                  {'old_health_monitor': old_health_monitor,
                   'health_monitor': health_monitor, 'pool_id': pool_id})

        self.client.update_health_monitor(context, old_health_monitor['id'],
                                          health_monitor)
        self.plugin.update_status(context, ldb.HealthMonitor,
                                  old_health_monitor["id"], constants.ACTIVE)

        LOG.debug("MidonetLoadbalancerDriver.update_pool_health_monitor "
                  "exiting: health_monitor=%(health_monitor)r",
                  {'health_monitor': health_monitor})

    def stats(self, context, pool_id):
        raise NotImplementedError()
