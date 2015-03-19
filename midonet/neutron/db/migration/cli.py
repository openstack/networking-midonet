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

import os

from alembic import config as alembic_config
from midonet.neutron.db import task_db
from neutron.db.migration import cli as n_cli
from oslo_config import cfg
from oslo_serialization import jsonutils
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


CONF = n_cli.CONF


def get_session(connection):
    engine = create_engine(connection)
    Session = sessionmaker(bind=engine)
    return Session()


def task_list(config, cmd):
    connection = config.neutron_config.database.connection
    session = get_session(connection)
    printer = config.print_stdout
    line = "%-7s%-11s%-20s%-40s%-20s"
    printer(line, "id", "type", "data type", "resource id", "time")
    printer(line, "--", "----", "---------", "-----------", "----")

    def print_task(task):
        printer(line, task.id, task.type, task.data_type, task.resource_id,
                task.created_at)
    show_unprocessed = config.neutron_config.command.u
    tasks = task_db.get_task_list(session, show_unprocessed)
    [print_task(task) for task in tasks]


def task_clean(config, cmd):
    connection = config.neutron_config.database.connection
    session = get_session(connection)
    task_db.task_clean(session)


def task_resource(config, cmd):
    connection = config.neutron_config.database.connection
    session = get_session(connection)
    printer = config.print_stdout
    data = task_db.get_current_task_data(session)
    for data_type in data:
        printer(data_type + "S: \n")
        for res in data[data_type]:
            data_json = jsonutils.loads(data[data_type][res])
            printer(jsonutils.dumps(data_json, indent=4, sort_keys=True))


def data_show(config, cmd):
    pass


def data_readonly(config, cmd):
    pass


def data_readwrite(config, cmd):
    pass


def data_version_list(config, cmd):
    pass


def data_version_sync(config, cmd):
    pass


def data_version_activate(config, cmd):
    pass


def add_command_parsers(subparsers):
    n_cli.add_command_parsers(subparsers)
    parser = subparsers.add_parser('task-list')
    parser.add_argument('-u', action='store_true')
    parser.set_defaults(func=task_list)
    parser = subparsers.add_parser('task-clean')
    parser.set_defaults(func=task_clean)
    parser = subparsers.add_parser('task-resource')
    parser.set_defaults(func=task_resource)
    parser = subparsers.add_parser('data-show')
    parser.set_defaults(func=data_show)
    parser = subparsers.add_parser('data-readonly')
    parser.set_defaults(func=data_readonly)
    parser = subparsers.add_parser('data-readwrite')
    parser.set_defaults(func=data_readwrite)
    parser = subparsers.add_parser('data-version-list')
    parser.set_defaults(func=data_version_list)
    parser = subparsers.add_parser('data-version-sync')
    parser.set_defaults(func=data_version_sync)
    parser = subparsers.add_parser('data-version-activate')
    parser.set_defaults(func=data_version_activate)


command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help=_('Available commands'),
                                handler=add_command_parsers)

# Override the db management options with our own extended version
CONF.unregister_opt(n_cli.command_opt)
CONF.register_cli_opt(command_opt)


def get_alembic_config():
    config = alembic_config.Config(os.path.join(os.path.dirname(__file__),
                                                'alembic.ini'))
    config.set_main_option('script_location',
                           'midonet.neutron.db.migration:alembic_migration')
    return config


def main():
    config = get_alembic_config()
    # attach the Neutron conf to the Alembic conf
    config.neutron_config = CONF

    CONF(project='neutron')
    CONF.command.func(config, CONF.command.name)
