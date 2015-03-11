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

import collections
import datetime
from neutron.openstack.common import jsonutils
import sqlalchemy as sa

from neutron.common import exceptions as n_exc
from neutron.db import model_base

CREATE = 1
DELETE = 2
UPDATE = 3
FLUSH = 4

NETWORK = 1
SUBNET = 2
ROUTER = 3
PORT = 4
FLOATINGIP = 5
SECURITYGROUP = 6
SECURITYGROUPRULE = 7
POOL = 8
VIP = 9
HEALTHMONITOR = 10
MEMBER = 11


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
    data = sa.Column(sa.Text(length = 2 ** 24))
    resource_id = sa.Column(sa.String(36))
    transaction_id = sa.Column(sa.String(40))
    created_at = sa.Column(sa.DateTime(), default=datetime.datetime.utcnow)


def create_task(context, task_type_id, task_id=None, data_type_id=None,
                resource_id=None, data=None):

    with context.session.begin(subtransactions=True):
        db = Task(id=task_id,
                  type_id=task_type_id,
                  data_type_id=data_type_id,
                  data=None if data is None else jsonutils.dumps(data),
                  resource_id=resource_id,
                  transaction_id=context.request_id)
        context.session.add(db)


class MidonetClusterException(n_exc.NeutronException):
    message = _("Midonet Cluster Error: %(msg)s")


class MidoClusterMixin(object):

    def create_cluster(self, context, cluster):
        try:
            # lock the entire database so we can take a snapshot of the
            # data we need.
            context.session.execute('FLUSH TABLES WITH READ LOCK')

            database = collections.OrderedDict({
                NETWORK: self.get_networks(context),
                SUBNET: self.get_subnets(context),
                PORT: self.get_ports(context),
                ROUTER: self.get_routers(context),
                FLOATINGIP: self.get_floatingips(context),
                SECURITYGROUP: self.get_security_groups(context),
                SECURITYGROUPRULE: self.get_security_group_rules(context),
                POOL: self.get_pools(context),
                VIP: self.get_vips(context),
                HEALTHMONITOR: self.get_health_monitors(context),
                MEMBER: self.get_members(context)})

            # record how much items we have processed so far. We compare
            # this to another count after we lock midonet_tasks to make
            # sure nothing snuck in between the locks.
            task_count = context.session.query(Task).count()
        finally:
            context.session.execute('UNLOCK TABLES')

        try:
            context.session.execute('LOCK TABLES midonet_tasks WRITE')
            with context.session.begin(subtransactions=True):
                if task_count != context.session.query(Task).count():
                    error_msg = ("The database has been updated while the "
                                 "rebuild operation is in progress")
                    raise MidonetClusterException(msg=error_msg)

                context.session.execute('TRUNCATE TABLE midonet_tasks')

                create_task(context, FLUSH, task_id=1)
                for key in database:
                    for item in database[key]:
                        create_task(context, CREATE, data_type_id=key,
                                    resource_id=item['id'], data=item)
        finally:
            context.session.execute('UNLOCK TABLES')
        # Neutron assumes that any create_* call returns a dictionary. Even
        # though we do nothing with 'cluster', we still return it back to
        # neutron to satisfy this assumption.
        return cluster
