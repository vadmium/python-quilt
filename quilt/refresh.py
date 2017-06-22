# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012 - 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from quilt.command import Command
from quilt.db import Db, Series, _get_top
from quilt.error import QuiltError
from quilt.patch import Patch, Diff, _generate_patch
from quilt.signals import Signal
from quilt.utils import Directory, File, TmpFile


class Refresh(Command):
    """ Command class to refresh (add or remove chunks) a patch
    """

    edit_patch = Signal()
    refreshed = Signal()

    def __init__(self, cwd, quilt_pc, quilt_patches):
        super(Refresh, self).__init__(cwd)
        self.quilt_pc = Directory(quilt_pc)
        self.quilt_patches = Directory(quilt_patches)
        self.db = Db(quilt_pc)
        self.series = Series(quilt_patches)

    def refresh(self, patch_name=None, edit=False):
        """ Refresh patch with patch_name or applied top patch if patch_name is
        None
        """
        if patch_name:
            patch = Patch(patch_name)
        else:
            patch = _get_top(self.db)

        pc_dir = self.quilt_pc + patch.get_name()
        patch_file = self.quilt_patches + File(patch.get_name())

        with TmpFile(prefix="pquilt-") as tmpfile:
            f = tmpfile.open()
            _generate_patch(self.cwd, self.db, self.series.dirname, f, patch)

            if tmpfile.is_empty():
                raise QuiltError("Nothing to refresh.")

            if edit:
                self.edit_patch(tmpfile)
                tpatch = Patch(tmpfile.get_name())
                tpatch.run(pc_dir.get_name(), dry_run=True, quiet=True)

            if patch_file.exists():
                diff = Diff(patch_file, tmpfile)
                if diff.equal(self.cwd):
                    raise QuiltError("Nothing to refresh.")

            tmpfile.copy(patch_file)

        timestamp = pc_dir + File(".timestamp")
        timestamp.touch()

        refresh = self.quilt_pc + File(patch.get_name() + "~refresh")
        refresh.delete_if_exists()

        self.refreshed(patch)
