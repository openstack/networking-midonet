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

import time

from neutron import i18n
from oslo_log import log as logging


LOG = logging.getLogger(__name__)
_LW = i18n._LW


def retry_on_error(attempts, delay, error_cls):
    """Decorator for error handling retry logic

    This decorator retries the function specified number of times with
    specified delay between each attempt, for every exception thrown specified
    in error_cls.  If case the retry fails in all attempts, the error_cls
    exception object is thrown.

    :param attempts: Number of retry attempts
    :param delay: Delay in seconds between attempts
    :param error_cls: The exception class that triggers a retry attempt
    """
    def internal_wrapper(func):
        def retry(*args, **kwargs):
            err = None
            for i in range(attempts):
                try:
                    return func(*args, **kwargs)
                except error_cls as exc:
                    LOG.warn(_LW('Retrying because of error: %r'), exc)
                    time.sleep(delay)
                    err = exc
            # err should always be set to a valid exception object
            assert isinstance(err, error_cls)
            raise err
        return retry
    return internal_wrapper
