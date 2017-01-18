# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

import os

from quilt.add import Add
from quilt.cli.meta import Command

class AddCommand(Command):
    """ Mark files to be included in a patch """

    name = "add"

    params = dict(
        args=dict(metavar="file", nargs="+"),
        patch=dict(name="-p", help="patch to add files to"),
    )
    def run(self, args, patch=None):
        add = Add(os.getcwd(), self.get_pc_dir(), self.get_patches_dir())
        add.file_added.connect(self.file_added)
        add.add_files(args, patch)

    def file_added(self, file, patch):
        print("File %s added to patch %s" % (file.get_name(), patch.get_name()))
