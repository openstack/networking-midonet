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
from neutron.common import constants as n_const
from neutron.db import l3_db
from neutron.db import models_v2
from neutron_lbaas.db.loadbalancer import loadbalancer_db as lb_db
from sqlalchemy.orm import exc


def get_by_model_id(context, model, object_id):
    objects = context.session.query(model)
    objects = objects.filter(model.id == object_id)
    try:
        return objects.one()
    except exc.NoResultFound:
        return None


def get_network(context, network_id):
    return get_by_model_id(context, models_v2.Network, network_id)


def get_subnet(context, subnet_id):
    return get_by_model_id(context, models_v2.Subnet, subnet_id)


def get_pool(context, pool_id):
    return get_by_model_id(context, lb_db.Pool, pool_id)


def is_subnet_external(context, subnet):
    network = get_network(context, subnet['network_id'])
    assert network is not None
    return network.external


def get_router_from_subnet(context, subnet):
    iport = get_router_interface_port(context, subnet)
    if iport is None:
        return None
    else:
        return get_router_from_port(context, iport)


def get_router_from_pool(context, pool_id):
    pool = get_pool(context, pool_id)
    if pool is None:
        return None

    subnet = get_subnet(context, pool.subnet_id)
    if subnet is None:
        return None

    return get_router_from_subnet(context, subnet)


def get_router_from_port(context, port_id):
    routers = context.session.query(l3_db.Router)
    routers = routers.join(models_v2.Port,
                           l3_db.Router.id == models_v2.Port.device_id)
    routers = routers.filter(models_v2.Port.id == port_id)
    try:
        return routers.one().id
    except exc.NoResultFound:
        return None


def get_router_interface_port(context, subnet):
    all_ports = context.session.query(models_v2.Port).join(
        models_v2.Port.fixed_ips)
    ports = all_ports.filter(
        models_v2.Port.device_owner == n_const.DEVICE_OWNER_ROUTER_INTF)
    ports = ports.filter(models_v2.Port.network_id == subnet['network_id'])
    ports = ports.filter(
        models_v2.IPAllocation.ip_address == subnet['gateway_ip'])
    try:
        return ports.one().id
    except exc.NoResultFound:
        return None
