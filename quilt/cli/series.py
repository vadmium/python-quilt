# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from quilt.cli.meta import Command
from quilt.db import Db, Series

class SeriesCommand(Command):
    """ List all applied and unapplied patches
    """

    name = "series"

    def run(self, *, v=False):
        series = Series(self.get_patches_dir())
        if v:
            db = Db(self.get_pc_dir())
            applied = db.patches()
            for patch in applied[:-1]:
                print("+ " + patch.get_name())
            if applied:
                print("= " + applied[-1].get_name())
                patches = series.patches_after(applied[-1])
            else:
                patches = series.patches()
            for patch in patches:
                print("  " + patch.get_name())
        else:
            for patch in series.patches():
                print(patch.get_name())
