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

from neutron.tests import base

from midonet.neutron.common import util


class UtilTestCase(base.BaseTestCase):
    """Test for midonet.neutron.common.util."""

    def setUp(self):
        super(UtilTestCase, self).setUp()

    def test_retry_on_error(self):
        retry_num = 2

        class TestClass(object):

            def __init__(self):
                self.attempt = 0

            @util.retry_on_error(retry_num, 1, ValueError)
            def test(self):
                self.attempt += 1
                raise ValueError

        test_obj = TestClass()
        try:
            test_obj.test()
            # should never reach here
            self.assertTrue(False)
        except ValueError:
            pass

        self.assertEqual(retry_num, test_obj.attempt)
