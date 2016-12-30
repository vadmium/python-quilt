#!/usr/bin/env python
# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2017 Björn Ricks <bjoern.ricks@gmail.com>
#
# See LICENSE comming with the source of python-quilt for details.

from contextlib import contextmanager
import os, os.path
import six

from helpers import QuiltTest, make_file, tmp_series

from quilt.error import QuiltError
from quilt.patch import Patch
from quilt.push import Push
from quilt.utils import Directory, TmpDirectory, File

test_dir = os.path.dirname(__file__)


class PushTest(QuiltTest):

    data_dir = Directory(os.path.join(test_dir, "data", "push"))

    def test_apply_all(self):
        patch2 = Patch("p2.patch")

        test_dir = self.data_dir + "test1"

        with TmpDirectory(dir=self.data_dir.get_name()) as tmp_dir:
            tmp_test_dir = tmp_dir + "test1"
            test_dir.copy(tmp_test_dir)

            pc_dir = tmp_test_dir + "pc"
            patches_dir = tmp_test_dir + "patches"

            f1 = tmp_test_dir + File("f1")
            self.assertFalse(f1.exists())
            f2 = tmp_test_dir + File("f2")
            self.assertFalse(f2.exists())

            push = Push(tmp_test_dir.get_name(), pc_dir.get_name(),
                        patches_dir.get_name())

            self.assertIsNone(push.db.top_patch())
            push.apply_all(quiet=True)
            self.assertEqual(patch2, push.db.top_patch())

            self.assertTrue(f1.exists())
            self.assertTrue(f2.exists())

    def test_apply_next(self):
        patch1 = Patch("p1.patch")
        patch2 = Patch("p2.patch")

        test_dir = self.data_dir + "test2"

        with TmpDirectory(dir=self.data_dir.get_name()) as tmp_dir:
            tmp_test_dir = tmp_dir + "test2"
            test_dir.copy(tmp_test_dir)

            pc_dir = tmp_test_dir + "pc"
            patches_dir = tmp_test_dir + "patches"

            f1 = tmp_test_dir + File("f1")
            self.assertFalse(f1.exists())
            f2 = tmp_test_dir + File("f2")
            self.assertFalse(f2.exists())

            push = Push(tmp_test_dir.get_name(), pc_dir.get_name(),
                        patches_dir.get_name())
            self.assertIsNone(push.db.top_patch())

            push.apply_next_patch(quiet=True)
            self.assertEqual(patch1, push.db.top_patch())

            self.assertTrue(f1.exists())
            self.assertFalse(f2.exists())

            push.apply_next_patch(quiet=True)
            self.assertEqual(patch2, push.db.top_patch())

            self.assertTrue(f1.exists())
            self.assertTrue(f2.exists())
    
    def test_force(self):
        with tmp_series() as [dir, series]:
            self._make_conflict(dir, series)
            series.save()
            cmd = Push(dir, quilt_pc=dir, quilt_patches=series.dirname)
            with six.assertRaisesRegex(
                        self, QuiltError, r"does not apply"), \
                    self._suppress_output():
                cmd.apply_next_patch(quiet=True)
            with six.assertRaisesRegex(self, QuiltError,
                        r"Applied patch.*needs refresh"), \
                    self._suppress_output():
                cmd.apply_next_patch(quiet=True, force=True)
    
    def test_without_refresh(self):
        with tmp_series() as [dir, series]:
            self._make_conflict(dir, series)
            series.add_patch("p2")
            series.save()
            cmd = Push(dir, quilt_pc=dir, quilt_patches=series.dirname)
            with six.assertRaisesRegex(self, QuiltError,
                        r"Applied patch.*needs refresh"), \
                    self._suppress_output():
                cmd.apply_next_patch(quiet=True, force=True)
            with six.assertRaisesRegex(self, QuiltError,
                    r"needs to be refreshed"):
                cmd.apply_next_patch()
    
    def _make_conflict(self, dir, series):
        series.add_patch(Patch("conflict.patch"))
        make_file(
            b"--- orig/file\n"
            b"+++ new/file\n"
            b"@@ -1 +1 @@\n"
            b"-old\n"
            b"+new\n", series.dirname, "conflict.patch")
        make_file(b"conflict\n", dir, "file")
    
    @contextmanager
    def _suppress_output(self):
        """ Silence error messages from the "patch" command """
        STDOUT_FILENO = 1
        STDERR_FILENO = 2
        with open(os.devnull, "w") as null:
            stdout = os.dup(STDOUT_FILENO)
            stderr = os.dup(STDERR_FILENO)
            os.dup2(null.fileno(), STDOUT_FILENO)
            os.dup2(null.fileno(), STDERR_FILENO)
        try:
            yield
        finally:
            os.dup2(stdout, STDOUT_FILENO)
            os.dup2(stderr, STDERR_FILENO)
            os.close(stdout)
            os.close(stderr)


if __name__ == "__main__":
    PushTest.run_tests()
