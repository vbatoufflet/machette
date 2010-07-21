#!/usr/bin/env python
# -*- coding: utf-8 -*-
# $Id$

# Append base directory to the PYTHONPATH
import os, sys

BASE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir)
sys.path.insert(0, BASE_DIR)

# Generate manpages
from docutils.core import publish_file
from docutils.writers.manpage import Writer

for manpage in [ 'machette.1' ]:
	publish_file(
		writer=Writer(),
		source_path='%s/doc/%s.rst' % (BASE_DIR, manpage),
		destination_path='%s/doc/%s' % (BASE_DIR, manpage),
	)
