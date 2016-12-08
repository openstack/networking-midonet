# Copyright 2015 Midokura SARL
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

import datetime

from neutron_lib.db import model_base
from oslo_serialization import jsonutils
from oslo_utils import uuidutils
import sqlalchemy as sa

import midonet.neutron.db.data_state_db as ds_db

CONF_ID = '00000000-0000-0000-0000-000000000001'

CREATE = "CREATE"
DELETE = "DELETE"
UPDATE = "UPDATE"
FLUSH = "FLUSH"

NETWORK = "NETWORK"
SUBNET = "SUBNET"
ROUTER = "ROUTER"
PORT = "PORT"
FLOATING_IP = "FLOATINGIP"
SECURITY_GROUP = "SECURITYGROUP"
SECURITY_GROUP_RULE = "SECURITYGROUPRULE"
POOL = "POOL"
VIP = "VIP"
HEALTH_MONITOR = "HEALTHMONITOR"
MEMBER = "MEMBER"
PORT_BINDING = "PORTBINDING"
CONFIG = "CONFIG"


OP_IMPORT = 'IMPORT'
OP_FLUSH = 'FLUSH'


TASK_STATE_TABLE = 'midonet_task_state'


class Task(model_base.BASEV2, model_base.HasProjectNoIndex):
    __tablename__ = 'midonet_tasks'

    id = sa.Column(sa.Integer(), primary_key=True)
    type = sa.Column(sa.String(length=36))
    data_type = sa.Column(sa.String(length=36))
    data = sa.Column(sa.Text())
    resource_id = sa.Column(sa.String(36))
    transaction_id = sa.Column(sa.String(40), nullable=False)
    created_at = sa.Column(sa.DateTime(), default=datetime.datetime.utcnow,
                           nullable=False)


def get_current_task_data(session):
    data = dict()
    for task in session.query(Task):
        if task.data_type not in data:
            data[task.data_type] = dict()
        if task.type == DELETE:
            data[task.data_type].pop(task.resource_id, None)
        else:
            data[task.data_type][task.resource_id] = task.data
    return data


def get_task_list(session, show_unprocessed):
    tasks = session.query(Task)
    if show_unprocessed:
        task_state = session.query(ds_db.DataState).one()
        lp_id = task_state.last_processed_id
        if lp_id is not None:
            tasks = tasks.filter(Task.id > lp_id)
    return tasks


def task_clean(session):
    task_state = session.query(ds_db.DataState).one()
    lp_id = task_state.last_processed_id
    task_state.update({'last_processed_id': None,
                       'updated_at': datetime.datetime.utcnow()})
    session.query(Task).filter(Task.id <= lp_id).delete()
    session.commit()


def create_task(context, type, task_id=None, data_type=None,
                resource_id=None, data=None):

    with context.session.begin(subtransactions=True):
        db = Task(id=task_id,
                  type=type,
                  tenant_id=context.tenant,
                  data_type=data_type,
                  data=None if data is None else jsonutils.dumps(data),
                  resource_id=resource_id,
                  transaction_id=context.request_id)
        context.session.add(db)


def create_config_task(session, data):
    data['id'] = CONF_ID
    with session.begin(subtransactions=True):
        db = Task(type=CREATE,
                  tenant_id=None,
                  data_type=CONFIG,
                  data=jsonutils.dumps(data),
                  resource_id=data['id'],
                  transaction_id=uuidutils.generate_uuid())
        session.add(db)


def create_port_binding_task(context, port_id, interface_name, host):
    data = {
        'id': port_id,
        'host_id': host,
        'interface_name': interface_name,
        'port_id': port_id
    }
    create_task(context, CREATE, data_type=PORT_BINDING, resource_id=port_id,
                data=data)


def delete_port_binding_task(context, port_id):
    create_task(context, DELETE, data_type=PORT_BINDING, resource_id=port_id)
