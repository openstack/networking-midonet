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

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron_lbaas.drivers import driver_base

from midonet.neutron.client import base as c_base
from midonet.neutron.common import utils

LOG = logging.getLogger(__name__)


class MidonetLoadBalancerDriver(driver_base.LoadBalancerBaseDriver):

    def __init__(self, plugin):
        super(MidonetLoadBalancerDriver, self).__init__(plugin)

        self.load_balancer = MidonetLoadBalancerManager(self)
        self.listener = MidonetListenerManager(self)
        self.pool = MidonetPoolManager(self)
        self.member = MidonetMemberManager(self)
        self.health_monitor = MidonetHealthMonitorManager(self)
        self._client = c_base.load_client(cfg.CONF.MIDONET)


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
    pass


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
