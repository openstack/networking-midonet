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

import mock
import random

from oslo_utils import uuidutils

from neutronclient.tests.unit.osc.v2 import fakes

from midonet.osc import logging_resource


def _generate_resource():
    return {
        'id': uuidutils.generate_uuid(),
        'name': 'name-' + uuidutils.generate_uuid(),
        'enabled': random.choice([True, False]),
    }


def _id_for(name_or_id):
    return 'ID-for-' + name_or_id


def _mock_get_id():
    def _get_id(client, name_or_id):
        return _id_for(name_or_id)

    mock.patch('midonet.osc.logging_resource._get_id', _get_id).start()


class TestCreateLoggingResource(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        self._resource = {
            'id': uuidutils.generate_uuid(),
        }
        super(TestCreateLoggingResource, self).setUp()
        self.neutronclient.create_logging_resource = mock.Mock(
            return_value={'logging_resource': self._resource})
        self.cmd = logging_resource.CreateLoggingResource(self.app,
                                                          self.namespace)

    def test_create(self):
        arglist = [
            '--enable', '--description', 'my log', 'mine',
        ]
        verifylist = [
            ('name', 'mine'),
            ('description', 'my log'),
            ('enable', True),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        request = {
            'name': 'mine',
            'description': 'my log',
            'enabled': True,
        }
        self._resource.update(request)
        columns, data = self.cmd.take_action(parsed_args)
        self.neutronclient.create_logging_resource.assert_called_once_with({
            'logging_resource': request,
        })
        expected_columns = ('description', 'enabled', 'id', 'name',)
        expected_data = tuple(self._resource[key] for key in expected_columns)
        self.assertEqual(expected_columns, columns)
        self.assertEqual(expected_data, data)


class TestDeleteLoggingResource(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestDeleteLoggingResource, self).setUp()
        self.neutronclient.delete_logging_resource = mock.Mock()
        self.cmd = logging_resource.DeleteLoggingResource(self.app,
                                                          self.namespace)
        _mock_get_id()

    def test_delete(self):
        arglist = [
            'mine', 'yours',
        ]
        verifylist = [
            ('logging_resource', arglist),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.assertIsNone(result)
        self.neutronclient.delete_logging_resource.assert_has_calls([
            mock.call(_id_for(id_)) for id_ in arglist
        ])


class TestListLoggingResource(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        self._resources = [_generate_resource() for i in range(1, 16)]
        super(TestListLoggingResource, self).setUp()
        self.neutronclient.list_logging_resources = mock.Mock(
            return_value={'logging_resources': self._resources})
        self.cmd = logging_resource.ListLoggingResource(self.app,
                                                       self.namespace)
        _mock_get_id()

    def test_list(self):
        arglist = []
        verifylist = []
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        expected_columns = ('ID', 'Name',)
        expected_data = [
            tuple(resource[key.lower()] for key in expected_columns)
            for resource in self._resources
        ]
        self.assertEqual(expected_columns, columns)
        self.assertEqual(expected_data, list(data))


class TestSetLoggingResource(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        super(TestSetLoggingResource, self).setUp()
        self.neutronclient.update_logging_resource = mock.Mock()
        self.cmd = logging_resource.SetLoggingResource(self.app,
                                                       self.namespace)
        _mock_get_id()

    def test_set(self):
        arglist = [
            '--name', 'new-name',
            '--description', 'new description',
            'old-name',
        ]
        verifylist = [
            ('logging_resource', 'old-name'),
            ('description', 'new description'),
            ('name', 'new-name'),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        result = self.cmd.take_action(parsed_args)
        self.assertIsNone(result)
        self.neutronclient.update_logging_resource.assert_called_once_with(
            _id_for('old-name'), {'logging_resource': {
                'name': 'new-name',
                'description': 'new description',
            }})


class TestShowLoggingResource(fakes.TestNeutronClientOSCV2):
    def setUp(self):
        self._resource = _generate_resource()
        super(TestShowLoggingResource, self).setUp()
        self.neutronclient.show_logging_resource = mock.Mock(
            return_value={'logging_resource': self._resource})
        self.cmd = logging_resource.ShowLoggingResource(self.app,
                                                        self.namespace)
        _mock_get_id()

    def test_show(self):
        arglist = [
            self._resource['name'],
        ]
        verifylist = [
            ('logging_resource', self._resource['name']),
        ]
        parsed_args = self.check_parser(self.cmd, arglist, verifylist)
        columns, data = self.cmd.take_action(parsed_args)
        expected_columns = ('enabled', 'id', 'name',)
        expected_data = tuple(self._resource[key] for key in expected_columns)
        self.assertEqual(expected_columns, columns)
        self.assertEqual(expected_data, data)
