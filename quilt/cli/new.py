# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from quilt.cli.meta import Command
from quilt.error import PatchAlreadyExists
from quilt.new import New

class NewCommand(Command):
    """ Add a blank unapplied patch to the series """

    name = "new"

    def run(self, patchname):
        new = New(self.get_cwd(), self.get_pc_dir(), self.get_patches_dir())
        try:
            new.create(patchname)
        except PatchAlreadyExists as e:
            print(e)
