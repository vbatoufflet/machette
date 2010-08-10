# -*- coding: utf-8 -*-
#
# This file is a part of Machette.
#
# Copyright (C) 2010 Vincent Batoufflet <vincent@batoufflet.info>
#
# This software is released under the terms of the GNU General Public License
# version 3 or any later version. See LICENSE file for further details.
#
# $Id$

import os
from machette import __author__, __email__, __website__

__MODULES__ = list()


class MachetteModule:
    def __init__(self, parent):
        """
        Initialize MachetteModule instance
            MachetteModule __init__(parent instance: Machette)
        """

        # Set instance attributes
        self.parent = parent

    def register(self):
        """
        Register MachetteModule module
            void register(void)
        """

        pass

    def unregister(self):
        """
        Unregister MachetteModule module
            void unregister(void)
        """

        pass


def get_modules_list():
    """
    Get the list of available modules
        list get_modules_list(void)
    """

    # Probe for available modules
    if len(__MODULES__) == 0:
        for name in os.listdir(os.path.dirname(__file__)):
            # Skip unwanted files
            if not name.endswith('.py') \
              or name.startswith('.') \
              or name.startswith('_'):
                continue

            # Append found module
            __MODULES__.append(os.path.splitext(name)[0])

    return __MODULES__


def load_module(name, fromlist=[]):
    """
    Load a module by name
        object load_module(module name: str, from list: list)
    """

    try:
        # Try to import the module
        return __import__('machette.module.%s' % name, globals(), locals(),
            fromlist)
    except ImportError:
        # Return None on failure
        return None
