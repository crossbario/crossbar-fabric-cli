# -*- coding: utf-8 -*-
#

project = 'sphinxcontrib_xbr test'
copyright = '2018, Crossbar.io Technologies and contributors'
author = 'Crossbar.io Technologies and contributors'

version = '0.1.0'
release = version

extensions = [
    'sphinxcontrib.xbr',
]

source_suffix = '.rst'
master_doc = 'index'
language = None
pygments_style = 'sphinx'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
