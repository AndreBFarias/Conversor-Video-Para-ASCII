# Configuration file for the Sphinx documentation builder

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# Project information
project = 'Extase em 4R73'
copyright = '2026, Extase em 4R73 Team'
author = 'Extase em 4R73 Team'
release = '1.0.0'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'pt_BR'

# HTML output
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = f'{project} v{release}'
html_short_title = project
html_logo = '../../assets/icon.png'
html_favicon = '../../assets/icon.png'

# Napoleon settings (Google/NumPy docstring style)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'opencv': ('https://docs.opencv.org/4.x/', None),
}
