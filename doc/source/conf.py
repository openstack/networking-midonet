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
    'oslo_policy.sphinxext',
    'oslo_policy.sphinxpolicygen',
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
pygments_style = 'native'

# -- Options for HTML output --------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
# html_theme_path = ["."]
# html_theme = '_theme'
# html_static_path = ['static']

html_theme = 'openstackdocs'

# openstackdocstheme options
openstackdocs_repo_name = 'openstack/%s' % project
openstackdocs_pdf_link = True
openstackdocs_auto_name = False
openstackdocs_bug_project = project
openstackdocs_bug_tag = 'doc'

# Output file base name for HTML help builder.
htmlhelp_basename = '%sdoc' % project

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual], torctree_only).
latex_documents = [
    ('index',
     'doc-%s.tex' % project,
     u'Networking Midonet Documentation',
     u'OpenStack Foundation',
     'manual',
     # Specify toctree_only=True for a better document structure of
     # the generated PDF file.
     True),
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

# -- Options for oslo_policy.sphinxpolicygen ---------------------------------

policy_generator_config_file = '../../etc/oslo-policy-generator/policy.conf'
sample_policy_basename = '_static/networking-midonet'
