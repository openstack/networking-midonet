# -*- coding: utf-8 -*-
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

sys.path.insert(0, os.path.abspath('../..'))
# -- General configuration ----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    # 'sphinx.ext.autodoc',
    # 'sphinx.ext.intersphinx',
    'openstackdocstheme',
    'oslo_config.sphinxext',
]

# autodoc generation is a bit aggressive and a nuisance when doing heavy
# text edit cycles.
# execute "export SPHINX_DEBUG=1" in your terminal to disable

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'networking-midonet'
copyright = u'2015, OpenStack Foundation'

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
# html_theme_path = ["."]
# html_theme = '_theme'
# html_static_path = ['static']

html_theme = 'openstackdocs'

# openstackdocstheme options
repository_name = 'openstack/%s' % project
bug_project = project
bug_tag = 'doc'
html_last_updated_fmt = '%Y-%m-%d %H:%M'

# Output file base name for HTML help builder.
htmlhelp_basename = '%sdoc' % project

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
    ('index',
     '%s.tex' % project,
     u'%s Documentation' % project,
     u'OpenStack Foundation', 'manual'),
]

# Example configuration for intersphinx: refer to the Python standard library.
# intersphinx_mapping = {'http://docs.python.org/': None}

autodoc_mock_imports = [
    # NOTE(yamamoto): We don't have midonetclient in requirements.txt.
    'midonetclient',
    # NOTE(yamamoto): Avoid import-time side effects.
    #    Guru meditation now registers SIGUSR1 and SIGUSR2 by default
    #    for backward compatibility. SIGUSR1 will no longer be registered
    #    in a future release, so please use SIGUSR2 to generate reports.
    'oslo_reports',
    # "no IPRoute module for the platform" on OS X
    'neutron.agent.linux.ip_lib',
]
