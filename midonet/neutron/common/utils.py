# Copyright (C) 2015 Midokura SARL.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import types

import six

from neutron_lib import constants as n_const

from neutron.common import exceptions as n_exc


def check_update_port(orig, new):
    device_owner = new['device_owner']
    # REVISIT(yamamoto): The empty device_owner is allowed here because
    # it's assumed by many of unit tests and tempest.
    if (new['fixed_ips'] != orig['fixed_ips'] and
        not (device_owner.startswith(n_const.DEVICE_OWNER_COMPUTE_PREFIX) or
             device_owner.startswith(n_const.DEVICE_OWNER_ROUTER_INTF) or
             device_owner == '')):
        raise n_exc.UnsupportedPortDeviceOwner(op='fixed_ips update',
                                               port_id=new['id'],
                                               device_owner=device_owner)


def unboundmethod(func, cls):
    if six.PY3:
        # python 3.x doesn't have unbound methods
        func.__qualname__ = cls.__qualname__ + '.' + func.__name__  # PEP 3155
        return func
    else:  # python 2.x
        return types.MethodType(func, None, cls)
