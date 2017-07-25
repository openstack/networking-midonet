# Copyright (C) 2017 Midokura SARL.
# All rights reserved.
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

from flake8_import_order import styles


class OpenStack(styles.PEP8):
    # We use application-package-names for OpenStack packages which
    # are not libraries.
    # See [flake8] section in tox.ini.
    # https://github.com/PyCQA/flake8-import-order#extending-styles
    accepts_application_package_names = True
