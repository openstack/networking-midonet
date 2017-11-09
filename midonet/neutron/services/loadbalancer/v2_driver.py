# Copyright (C) 2016 Midokura SARL
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

# lbaasv2 driver for MidoNet

from neutron_lib import context as ncontext
from neutron_lib.plugins import directory

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_service import loopingcall

from neutron_lbaas.db.loadbalancer import models
from neutron_lbaas.drivers import driver_base
from neutron_lbaas.services.loadbalancer import constants as lb_const

from midonet.neutron.client import base as c_base
from midonet.neutron.common import config  # noqa
from midonet.neutron.common import utils

LOG = logging.getLogger(__name__)


# TODO(yamamoto): Introduce LBaaS PRECOMMIT callbacks and
# subscribe them for task-based api.


MN_STATUS_TO_OPERATING_STATUS = {
    'ACTIVE': lb_const.ONLINE,
    'INACTIVE': lb_const.OFFLINE,
    'NO_MONITOR': lb_const.NO_MONITOR,
}


class MidonetLoadBalancerDriver(driver_base.LoadBalancerBaseDriver):

    def __init__(self, plugin):
        super(MidonetLoadBalancerDriver, self).__init__(plugin)

        self.load_balancer = MidonetLoadBalancerManager(self)
        self.listener = MidonetListenerManager(self)
        self.pool = MidonetPoolManager(self)
        self.member = MidonetMemberManager(self)
        self.health_monitor = MidonetHealthMonitorManager(self)
        self._client = c_base.load_client(cfg.CONF.MIDONET)

        self.member_update_thread = loopingcall.FixedIntervalLoopingCall(
            self._update_member_status)
        self.member_update_thread.start(5, initial_delay=None,
                                        stop_on_exception=False)

        self.admin_ctx = ncontext.get_admin_context()

    def _update_member_status(self):
        # Request a list of pool members from the Midonet API
        # Go through this member list and update the neutron DB with each
        # pool member's status.
        db_members = self.plugin.db.get_pool_members(context=self.admin_ctx)
        for m in db_members:
            member_id = m.id
            midonet_member = self._client.get_pool_member(
                self.admin_ctx, member_id)
            LOG.debug("backend member: %(member)s", {'member': midonet_member})
            midonet_status = midonet_member['status']
            new_status = MN_STATUS_TO_OPERATING_STATUS[midonet_status]
            self.plugin.db.update_status(
                context=self.admin_ctx, model=models.MemberV2,
                id=member_id, operating_status=new_status)


def _build_func(method, client_method):
    if method == 'update':
        def f(self, context, old_obj, obj, **kwargs):
            return getattr(self.driver._client, client_method)(
                context=context, old_obj=old_obj, obj=obj, **kwargs)
    else:
        def f(self, context, obj, **kwargs):
            return getattr(self.driver._client, client_method)(
                context=context, obj=obj, **kwargs)
    f.__name__ = method
    return f


def _build_methods(cls, resource):
    # add methods like the following:
    #
    #    @driver_base.driver_op
    #    @log_helpers.log_method_call
    #    def <method>(self, context, obj):
    #        self._client.<method>_<resource>(context, obj)

    methods = ['create', 'update', 'delete']
    if resource == 'loadbalancerv2':
        methods += ['refresh', 'stats']
    for method in methods:
        client_method = method + '_' + resource
        f = _build_func(method, client_method)
        unbound = utils.unboundmethod(f, cls)
        wrapped = driver_base.driver_op(log_helpers.log_method_call(unbound))
        setattr(cls, method, wrapped)


def _build_manager_impl(resource):
    class _cls(object):
        pass

    _build_methods(_cls, resource)
    return _cls


class MidonetLoadBalancerManager(_build_manager_impl('loadbalancerv2'),
                                 driver_base.BaseLoadBalancerManager):

    # Override the create method here to ensure that the VIP port
    # associated with this load balancer has its 'admin_state_up' field
    # set to True. If it is set to False, midonet will not pass traffic
    # through the VIP.
    def create(self, context, obj, **kwargs):
        plugin = directory.get_plugin()
        plugin.update_port(context, obj.vip_port_id,
                           {'port': {'admin_state_up': True}})
        return super(MidonetLoadBalancerManager, self).create(
            context, obj, **kwargs)


class MidonetListenerManager(_build_manager_impl('listenerv2'),
                             driver_base.BaseListenerManager):
    pass


class MidonetPoolManager(_build_manager_impl('poolv2'),
                         driver_base.BasePoolManager):
    pass


class MidonetMemberManager(_build_manager_impl('memberv2'),
                           driver_base.BaseMemberManager):
    pass


class MidonetHealthMonitorManager(_build_manager_impl('healthmonitorv2'),
                                  driver_base.BaseHealthMonitorManager):
    pass
