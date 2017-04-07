#!/usr/bin/env python
# vim: fileencoding=utf-8 et sw=4 ts=4 tw=80:

# python-quilt - A Python implementation of the quilt patch system
#
# Copyright (C) 2012  Björn Ricks <bjoern.ricks@googlemail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA

from contextlib import contextmanager
import os, os.path
import six
import sys

from helpers import QuiltTest

test_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(test_dir, os.pardir))

from quilt.db import Series
from quilt.error import QuiltError, AllPatchesApplied
from quilt.patch import Patch
from quilt.push import Push
from quilt.utils import Directory, TmpDirectory, File

class PushTest(QuiltTest):

    data_dir = Directory(os.path.join(test_dir, "data", "push"))

    def test_apply_all(self):
        patch1 = Patch("p1.patch")
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

            self.assertEqual(None, push.db.top_patch())
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
            self.assertEqual(None, push.db.top_patch())

            push.apply_next_patch(quiet=True)
            self.assertEqual(patch1, push.db.top_patch())

            self.assertTrue(f1.exists())
            self.assertFalse(f2.exists())

            push.apply_next_patch(quiet=True)
            self.assertEqual(patch2, push.db.top_patch())

            self.assertTrue(f1.exists())
            self.assertTrue(f2.exists())
    
    def test_upto_applied(self):
        """ Push up to a specified patch when a patch is already applied """
        top = os.path.join(test_dir, "data", "pop", "test1")
        pc = os.path.join(top, "pc")
        patches = os.path.join(top, "patches")
        cmd = Push(top, quilt_pc=pc, quilt_patches=patches)
        self.assertRaises(AllPatchesApplied, cmd.apply_patch, "p1.patch")
    
    def test_force(self):
        with self._tmp_series() as [dir, series]:
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
        with self._tmp_series() as [dir, series]:
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
    
    @contextmanager
    def _tmp_series(self):
        with TmpDirectory() as dir:
            patches = os.path.join(dir.get_name(), "patches")
            os.mkdir(patches)
            yield (dir.get_name(), Series(patches))
    
    def _make_conflict(self, dir, series):
        series.add_patch(Patch("conflict.patch"))
        file = os.path.join(series.dirname, "conflict.patch")
        with open(file, "wb") as file:
            file.write(
                b"--- orig/file\n"
                b"+++ new/file\n"
                b"@@ -1 +1 @@\n"
                b"-old\n"
                b"+new\n"
            )
        with open(os.path.join(dir, "file"), "wb") as file:
            file.write(b"conflict\n")
    
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
