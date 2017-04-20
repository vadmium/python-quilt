from contextlib import contextmanager
import os, os.path

from helpers import make_file, tmp_series, swap_dir
from unittest import TestCase

import quilt.revert

from quilt.db import Db, Patch
from quilt.refresh import Refresh


class Test(TestCase):

    def test_unreverted(self):
        """ Test when the patch modifies unreverted files """
        with _set_up_patch() as [dir, series, originals]:
            make_file(b"unreverted original\n", originals, "unreverted")
            make_file(b"reverted original\n", originals, "reverted")
            make_file(b"unreverted patched\n", dir, "unreverted")
            make_file(b"reverted patched\n", dir, "reverted")
            Refresh(dir, quilt_pc=dir, quilt_patches=series).refresh()
            make_file(b"unreverted change\n", dir, "unreverted")
            make_file(b"reverted change\n", dir, "reverted")
            cmd = quilt.revert.Revert(dir,
                quilt_pc=dir, quilt_patches=series)
            cmd.revert_file("reverted")
            with open(os.path.join(dir, "reverted"), "rb") as file:
                self.assertEqual(file.read(), b"reverted patched\n")
            with open(os.path.join(dir, "unreverted"), "rb") as file:
                self.assertEqual(file.read(), b"unreverted change\n")

    def test_subdir(self):
        """ Revert a file in a subdirectory """
        with _set_up_patch() as [dir, series, originals]:
            os.mkdir(os.path.join(originals, "subdir"))
            make_file(b"original", originals, "subdir", "file")
            os.mkdir(os.path.join(dir, "subdir"))
            make_file(b"patched\n", dir, "subdir", "file")
            Refresh(dir, quilt_pc=dir, quilt_patches=series).refresh()
            make_file(b"changed\n", dir, "subdir", "file")
            oper = quilt.revert.Revert(dir,
                quilt_pc=dir, quilt_patches=series)
            oper.revert_file(os.path.join("subdir", "file"))
            with open(os.path.join(dir, "subdir", "file"), "rb") as file:
                self.assertEqual(file.read(), b"patched\n")

@contextmanager
def _set_up_patch():
    with tmp_series() as [dir, series], \
            swap_dir(dir):
        db = Db(dir)
        db.add_patch(Patch("patch"))
        db.save()
        originals = os.path.join(db.dirname, "patch")
        os.mkdir(originals)
        yield (dir, series.dirname, originals)
