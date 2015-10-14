Tests
-----

You can run the unit tests with the following command::

    $ ./run_tests.sh -f -V

``run_tests.sh`` installs its requirements to ``.venv`` on the initial run.
``-f`` forces a clean re-build of the virtual environment. If you just make
changes on the working tree without any change on the dependencies, you can
ignore ``-f`` switch.

``-V`` or ``--virtual-env`` is specified to use virtualenv and this should be
always turned on.


To know more detail about command options, please execute it with ``--help``::

    $ ./run_tests.sh --help
