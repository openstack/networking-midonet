# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright (C) 2014 Midokura SARL.
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

from neutron.api.v2 import base as api_base
from neutron.openstack.common import uuidutils
from neutron.tests import base

from midonet.neutron.common import util

CREATE = api_base.Controller.CREATE
DELETE = api_base.Controller.DELETE
LIST = api_base.Controller.LIST
SHOW = api_base.Controller.SHOW
UPDATE = api_base.Controller.UPDATE

_uuid = uuidutils.generate_uuid


class UtilTestCase(base.BaseTestCase):
    """Test for midonet.neutron.common.util."""
    def setUp(self):
        super(UtilTestCase, self).setUp()

    def _check_methods(self, cls):
        check_methods = [
            'get_%s' % cls.ALIAS,
            'get_%s' % util.PLURAL_NAME_MAP.get(
                cls.ALIAS, '%s' % cls.ALIAS),
            'create_%s' % cls.ALIAS,
            'update_%s' % cls.ALIAS,
            'delete_%s' % cls.ALIAS]
        for check_method in check_methods:
            self.assertIsNot(getattr(cls, check_method, None), None)

    def test_generate_methods(self):
        @util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
        class FooPlugin(object):
            """Foo plugin description."""

        self._check_methods(FooPlugin)

    def test_generated_methods_with_some_predefinitions(self):
        @util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
        class FooPlugin(object):
            """Foo plugin description."""
            def get_foo(self, context, foo, fields=None):
                return foo

        self._check_methods(FooPlugin)

        foo_plugin = FooPlugin()
        foo_id = _uuid()
        self.assertEqual(foo_plugin.get_foo(dict(), foo_id), foo_id)

    def test_generated_methods_without_some_predefinitions(self):
        @util.generate_methods(LIST, SHOW)
        class FooPlugin(object):
            """Foo plugin description."""

        self.assertIsNot(getattr(FooPlugin, 'get_foo', None), None)
        self.assertIsNot(getattr(FooPlugin, 'get_foos', None), None)

        self.assertIs(getattr(FooPlugin, 'create_foo', None), None)
        self.assertIs(getattr(FooPlugin, 'update_foo', None), None)
        self.assertIs(getattr(FooPlugin, 'delete_foo', None), None)

    def test_generated_methods_nested(self):
        @util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
        class FooPlugin(object):
            """Foo plugin description."""

        @util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
        class BarPlugin(object):
            """Bar, a child of Foo, plugin description."""
            PARENT = FooPlugin.ALIAS

        self._check_methods(FooPlugin)

        self.assertIsNot(getattr(BarPlugin, 'get_foo_bar', None), None)
        self.assertIsNot(getattr(BarPlugin, 'get_foo_bars', None), None)
        self.assertIsNot(getattr(BarPlugin, 'create_foo_bar', None), None)
        self.assertIsNot(getattr(BarPlugin, 'update_foo_bar', None), None)
        self.assertIsNot(getattr(BarPlugin, 'delete_foo_bar', None), None)

    def test_generated_methods_underscore(self):
        @util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
        class Foo_barPlugin(object):
            """Foo plugin description."""

        self.assertEqual(Foo_barPlugin.ALIAS, 'foo_bar')

        self._check_methods(Foo_barPlugin)

    def test_generated_methods_inheritance(self):
        @util.generate_methods(LIST, SHOW, CREATE, UPDATE, DELETE)
        class FooPlugin(object):
            """Foo plugin description."""

        @util.generate_methods(SHOW, UPDATE, DELETE)
        class BarOfFooPlugin(object):
            """Bar plugin description."""

        @util.generate_methods(LIST, CREATE)
        class BarPlugin(BarOfFooPlugin):
            """FooBar plugin description."""
            PARENT = FooPlugin.ALIAS

        self.assertEqual(FooPlugin.ALIAS, 'foo')

        self._check_methods(FooPlugin)

        self.assertIsNot(getattr(BarPlugin, 'get_bar', None), None)
        self.assertIsNot(getattr(BarPlugin, 'get_foo_bars', None), None)
        self.assertIsNot(getattr(BarPlugin, 'create_foo_bar', None), None)
        self.assertIsNot(getattr(BarPlugin, 'update_bar', None), None)
        self.assertIsNot(getattr(BarPlugin, 'delete_bar', None), None)
