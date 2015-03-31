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

import datetime
from neutron.db import model_base
import sqlalchemy as sa


DATA_VERSIONS_TABLE = 'midonet_data_versions'

STARTED = "STARTED"
COMPLETED = "COMPLETED"
ERROR = "ERROR"
ABORTED = "ABORTED"


class DataVersion(model_base.BASEV2):
    __tablename__ = DATA_VERSIONS_TABLE
    id = sa.Column(sa.Integer(), primary_key=True)
    sync_started_at = sa.Column(sa.DateTime())
    sync_finished_at = sa.Column(sa.DateTime())
    sync_status = sa.Column(sa.String(length=50))
    sync_tasks_status = sa.Column(sa.String(length=50))
    stale = sa.Column(sa.Boolean())


def get_last_version(session):
    data_versions = session.query(DataVersion)
    return data_versions.order_by(DataVersion.id.desc()).first()


def update_last_version_status(session, status):
    dv = get_last_version(session)
    dv.update({'sync_tasks_status': status})


def complete_last_version(session):
    update_last_version_status(session, COMPLETED)


def error_last_version(session):
    update_last_version_status(session, ERROR)


def abort_last_version(session):
    update_last_version_status(session, ABORTED)


def get_last_version_id(session):
    data_versions = session.query(DataVersion)
    dv = data_versions.order_by(DataVersion.id.desc()).first()
    if dv is None:
        return None
    else:
        return dv.id


def get_data_version_states(session):
    dv = session.query(DataVersion).order_by(DataVersion.id.desc()).first()
    if dv is None:
        return None, None
    else:
        return dv.sync_status, dv.sync_tasks_status


def get_data_versions(session):
    return session.query(DataVersion).all()


def create_data_version(session):
    data_version = DataVersion(sync_started_at=datetime.datetime.utcnow(),
                               sync_tasks_status=STARTED,
                               stale=False)
    session.add(data_version)
