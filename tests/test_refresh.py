# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# See LICENSE comming with the source of python-quilt for details.

import os, os.path

from helpers import make_file, swap_dir, tmp_series
from unittest import TestCase

import quilt.add
import quilt.refresh

from quilt.db import Db, Patch
from quilt.utils import TmpDirectory


class Test(TestCase):

    def test_refresh(self):
        with TmpDirectory() as dir, \
                swap_dir(dir.get_name()):
            db = Db(".pc")
            db.create()
            backup = os.path.join(".pc", "patch")
            os.mkdir(backup)
            make_file(b"", backup, "file")
            db.add_patch(Patch("patch"))
            db.save()
            make_file(b"", "patch")
            make_file(b"added\n", "file")
            cmd = quilt.refresh.Refresh(".", ".pc", ".")
            cmd.refresh()
            with open("patch", "r") as patch:
                self.assertTrue(patch.read(30))

    def test_add_subdir_nonexistent(self):
        """ Add a new file in a subdirectory to a patch """
        with tmp_series() as [dir, series], \
                swap_dir(dir):
            applied = Db(dir)
            applied.add_patch(Patch("test.patch"))
            applied.save()
            series.add_patches(applied.applied_patches())
            series.save()

            os.mkdir(os.path.join(dir, "subdir"))
            q = quilt.add.Add(dir, applied.dirname, series.dirname)
            q.add_file(os.path.join("subdir", "file"))
            make_file(b"contents\n", dir, "subdir", "file")
            q = quilt.refresh.Refresh(dir, applied.dirname, series.dirname)
            q.refresh()
            patch = os.path.join(series.dirname, "test.patch")
            with open(patch, "rb") as patch:
                patch = patch.read()
            self.assertIn(b"contents", patch)
