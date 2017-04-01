from contextlib import redirect_stdout
from io import StringIO
import os.path
from quilt.db import Series
from quilt.patch import Patch
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from helpers import QuiltTest

from quilt.delete import Delete
from quilt.cli.delete import DeleteCommand

class Test(QuiltTest):

    def test_next_first(self):
        """ Delete the next patch with only unapplied patches """
        with TemporaryDirectory() as dir:
            patches = Series(dir)
            patches.add_patch(Patch("patch"))
            patches.save()
            cmd = Delete(dir, dir, patches.dirname)
            cmd.delete_next()
            patches.read()
            self.assertTrue(patches.is_empty())
    
    def test_no_backup(self):
        """ Remove a patch without leaving a backup """
        with TemporaryDirectory() as dir:
            patches = Series(dir)
            patches.add_patch(Patch("patch"))
            patches.save()
            patch = os.path.join(dir, "patch")
            with open(patch, "wb"):
                pass
            with mock.patch.dict("os.environ", (
                ("QUILT_PATCHES", patches.dirname),
                ("QUILT_PC", dir),
            )), redirect_stdout(StringIO()):
                DeleteCommand().run(next=True, remove=True, backup=False)
            self.assertFalse(os.path.exists(patch))
            self.assertFalse(os.path.exists(patch + "~"))
