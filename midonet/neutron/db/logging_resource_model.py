# Copyright (C) 2016 Midokura SARL.
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

import sqlalchemy as sa
from sqlalchemy import orm

from neutron_lib.db import model_base

LOGGING_RESOURCES = 'midonet_logging_resources'
FIREWALL_LOGS = 'midonet_firewall_logs'


class LoggingResource(model_base.BASEV2, model_base.HasProjectNoIndex):
    """Represents a logging resource."""

    __tablename__ = LOGGING_RESOURCES
    id = sa.Column(sa.String(36), primary_key=True)
    name = sa.Column(sa.String(255))
    description = sa.Column(sa.String(1024))
    enabled = sa.Column(sa.Boolean, nullable=False)


class FirewallLog(model_base.BASEV2, model_base.HasProjectNoIndex):
    """Represents a firewall log."""

    __tablename__ = FIREWALL_LOGS

    id = sa.Column(sa.String(36), primary_key=True)
    logging_resource_id = sa.Column(
        sa.String(36),
        sa.ForeignKey('midonet_logging_resources.id', ondelete="CASCADE"),
        nullable=False)
    description = sa.Column(sa.String(1024))
    fw_event = sa.Column(sa.String(length=255), nullable=False)
    firewall_id = sa.Column(
        sa.String(36),
        sa.ForeignKey('firewalls.id', ondelete="CASCADE"),
        nullable=False)
    logging_resource = orm.relationship(
        LoggingResource,
        backref=orm.backref('firewall_logs', cascade='delete', lazy='joined'),
        primaryjoin="LoggingResource.id==FirewallLog.logging_resource_id")
