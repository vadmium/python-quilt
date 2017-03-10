# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

import os

from quilt.cli.meta import Command
from quilt.pop import Pop

class PopCommand(Command):

    name = "pop"

    def run(self, patch=None, *,
            all: dict(short="-a", help="remove all applied patches")
                = False):
        pop = Pop(os.getcwd(), self.get_pc_dir(), self.get_patches_dir())
        pop.unapplying.connect(self.unapplying)
        pop.unapplied.connect(self.unapplied)
        pop.empty_patch.connect(self.empty_patch)

        if all:
            pop.unapply_all()
        elif patch is None:
            pop.unapply_top_patch()
        else:
            pop.unapply_patch(patch)

    def unapplying(self, patch):
        print("Removing patch %s" % patch.get_name())

    def unapplied(self, patch):
        if not patch:
            print("No patches applied")
        else:
            print("Now at patch %s" % patch.get_name())

    def empty_patch(self, patch):
        print("Patch %s appears to be empty, removing" % patch.get_name())
