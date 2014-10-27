# Copyright 2014 Midokura SARL
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
import sqlalchemy as sa
import json

from neutron.db import model_base
from neutron.db import models_v2

CREATE = 1
DELETE = 2
UPDATE = 3

NETWORK = 1
SUBNET = 2
ROUTER = 3
PORT = 4
FLOATING_IP = 5
SECURITY_GROUP = 6
SECURTIY_GROUP_RULE = 7
ROUTER_INTERFACE = 8


class TaskType(model_base.BASEV2):
    __tablename__ = 'midonet_task_types'
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.String(50))


class DataType(model_base.BASEV2):
    __tablename__ = 'midonet_data_types'
    id = sa.Column(sa.Integer(), primary_key=True)
    name = sa.Column(sa.String(50))


class Task(model_base.BASEV2):
    __tablename__ = 'midonet_tasks'

    id = sa.Column(sa.Integer(), primary_key=True)
    type_id = sa.Column(sa.Integer(), sa.ForeignKey('midonet_task_types.id'))
    data_type_id = sa.Column(sa.Integer(),
                             sa.ForeignKey('midonet_data_types.id'))
    data = sa.Column(sa.Text(length=2**24))
    resource_id = sa.Column(sa.String(36))
    transaction_id = sa.Column(sa.String(40))
    created_at = sa.Column(sa.DateTime(), default=datetime.datetime.utcnow)


def create_task(context, task_type_id, data_type_id, resource_id, data):
    with context.session.begin(subtransactions=True):
        db = Task(type_id=task_type_id,
                  data_type_id=data_type_id,
                  data=json.dumps(data),
                  resource_id=resource_id,
                  transaction_id=context.request_id)
        context.session.add(db)
