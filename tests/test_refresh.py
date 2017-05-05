# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# See LICENSE comming with the source of python-quilt for details.

import os, os.path

from helpers import make_file, QuiltTest, swap_dir, tmp_series

import quilt.add
import quilt.refresh

from quilt.db import Db, Patch, Series


class Test(QuiltTest):

    def test_refresh(self):
        with tmp_series() as [dir, series], \
                swap_dir(dir):
            db = Db(".pc")
            db.create()
            backup = os.path.join(".pc", "patch")
            os.mkdir(backup)
            make_file(b"", backup, "file")
            db.add_patch(Patch("patch"))
            db.save()
            series.add_patches(db.applied_patches())
            series.save()
            make_file(b"added\n", "file")
            cmd = quilt.refresh.Refresh(".",
                ".pc", quilt_patches=series.dirname)
            cmd.refresh()
            with open(os.path.join(series.dirname, "patch"), "r") as patch:
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

    def test_patch_options(self):
        with tmp_series() as [dir, series]:
            make_file(b"test.patch -p0 -R\n", series.series_file)
            applied = Db(dir)
            applied.add_patch(Patch("test.patch"))
            applied.save()
            q = quilt.add.Add(dir, applied.dirname, series.dirname)
            q.add_file("test-file")
            make_file(b"contents\n", dir, "test-file")
            q = quilt.refresh.Refresh(dir, applied.dirname, series.dirname)
            q.refresh()
            self.assert_series_lines(series, (b"test.patch",))
